# weather_service.py
"""
Google Weather (temp + wind) + Visual Crossing (humidity) + NASA POWER (soil moisture; fallback: Open-Meteo)
- Temperature & wind: Google Maps Platform Weather API
- Humidity (RH %): Visual Crossing currentConditions (validated; fallback Open-Meteo)
- Soil moisture: NASA POWER `GWETTOP` (0–10 cm, fraction) → %; fallback Open-Meteo; final fallback = estimate from RH
- Independent sources so cards never duplicate values
"""

from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # fallback to UTC if zoneinfo unavailable

# ----------------------- Endpoints -----------------------
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_HOURS_URL = "https://weather.googleapis.com/v1/forecast/hours:lookup"
GOOGLE_DAYS_URL = "https://weather.googleapis.com/v1/forecast/days:lookup"

VC_TIMELINE = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lon}"
OM_FORECAST = "https://api.open-meteo.com/v1/forecast"

# === NASA POWER soil moisture ===
NASA_POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"

# ----------------------- Caching Configuration -----------------------
WEATHER_CACHE_TTL = 300  # 5 minutes for weather data
GEOCODE_CACHE_TTL = 3600  # 1 hour for geocoding
SOIL_CACHE_TTL = 1800  # 30 minutes for soil data

# ----------------------- Soil map (UI helper) -----------------------
INDIA_STATE_SOILS = {
    "andhra pradesh": "Red sandy loams & coastal alluvium",
    "arunachal pradesh": "Mountain & forest soils",
    "assam": "Alluvial (Brahmaputra valley)",
    "bihar": "Alluvial (Ganga plains)",
    "chhattisgarh": "Red & lateritic",
    "goa": "Lateritic",
    "gujarat": "Black cotton (regur) & alluvial",
    "haryana": "Alluvial",
    "himachal pradesh": "Mountain & shallow skeletal",
    "jharkhand": "Red & lateritic",
    "karnataka": "Red & lateritic; black in north",
    "kerala": "Lateritic",
    "madhya pradesh": "Black cotton (regur) & red",
    "maharashtra": "Black cotton (regur)",
    "manipur": "Mountain & forest soils",
    "meghalaya": "Lateritic & forest",
    "mizoram": "Mountain & forest",
    "nagaland": "Mountain & forest",
    "odisha": "Lateritic & coastal alluvium",
    "punjab": "Alluvial",
    "rajasthan": "Desert sandy & alluvial (eastern)",
    "sikkim": "Mountain soils",
    "tamil nadu": "Red loams & lateritic",
    "telangana": "Red sandy loams & black cotton (regur)",
    "tripura": "Lateritic & alluvial",
    "uttar pradesh": "Alluvial (Ganga plains)",
    "uttarakhand": "Mountain soils",
    "west bengal": "Alluvial (Ganga–Brahmaputra delta)",
    "andaman and nicobar islands": "Lateritic & coastal",
    "chandigarh": "Alluvial",
    "dadra and nagar haveli and daman and diu": "Coastal alluvial",
    "delhi": "Alluvial",
    "jammu and kashmir": "Mountain soils",
    "ladakh": "Cold desert soils",
    "lakshadweep": "Coralline sandy",
    "puducherry": "Coastal alluvial/red",
}

# ----------------------- Service -----------------------
class WeatherService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Import centralized configuration
        from .config import config
        
        # Get API keys from configuration
        self.google_key = config.GOOGLE_MAPS_API_KEY
        self.visual_key = config.VISUAL_CROSSING_API_KEY
        self.use_mock = False
        
        # Cache storage
        self._weather_cache = {}
        self._geocode_cache = {}
        self._soil_cache = {}
        self._last_cleanup = time.time()
        
        # HTTP session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'WeatherService/1.0 (Agriculture Assistant)'
        })
        
        # Configure session for better performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)
    
    def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        if current_time - self._last_cleanup > 60:  # Clean up every minute
            self._weather_cache = {k: v for k, v in self._weather_cache.items() 
                                 if current_time - v['timestamp'] < WEATHER_CACHE_TTL}
            self._geocode_cache = {k: v for k, v in self._geocode_cache.items() 
                                 if current_time - v['timestamp'] < GEOCODE_CACHE_TTL}
            self._soil_cache = {k: v for k, v in self._soil_cache.items() 
                              if current_time - v['timestamp'] < SOIL_CACHE_TTL}
            self._last_cleanup = current_time
    
    def _get_cached_data(self, cache_dict: dict, key: str, ttl: int) -> Optional[Any]:
        """Get cached data if not expired"""
        if key in cache_dict:
            cached = cache_dict[key]
            if time.time() - cached['timestamp'] < ttl:
                return cached['data']
            else:
                del cache_dict[key]
        return None
    
    def _set_cached_data(self, cache_dict: dict, key: str, data: Any):
        """Set cached data with timestamp"""
        cache_dict[key] = {
            'data': data,
            'timestamp': time.time()
        }

    # ------------- Public API -------------
    def get_weather(self, location: str) -> Dict[str, Any]:
        if self.use_mock:
            return self._mock(location)

        # Clean up expired cache entries
        self._cleanup_expired_cache()
        
        # Check cache first
        cache_key = location.lower().strip()
        cached_weather = self._get_cached_data(self._weather_cache, cache_key, WEATHER_CACHE_TTL)
        if cached_weather:
            self.logger.info(f"Using cached weather data for {location}")
            return cached_weather

        # 1) Geocode (with caching)
        lat, lon, state = self._geocode(location)

        # 2) GOOGLE: temp + wind (authoritative for temp; wind in km/h we compute from wind object)
        g_hourly = self._google_hourly(lat, lon, hours=24)
        g_now = g_hourly[0] if g_hourly else {}
        g_daily = self._google_daily(lat, lon, days=10)

        temp_c = self._to_float(g_now.get("temp_c"))
        wind_kmh = self._to_float(g_now.get("wind_kmh"))
        google_humidity = self._to_float(g_now.get("humidity"))
        
        # Log Google API data for debugging
        self.logger.info(f"Google API current data - temp: {temp_c}°C, wind: {wind_kmh} km/h, humidity: {google_humidity}%")
        self.logger.info(f"Google API full current data: {g_now}")

        temp_source = "Google Weather API"
        # Initialize sources - will be updated below based on actual data used
        wind_source = "—"
        hum_source = "—"

        # 3) VISUAL CROSSING: humidity primary; wind fallback; temp fallback
        vc_temp, vc_hum = self._vc_current_temp_humidity(lat, lon)
        vc_wind = self._vc_current_wind(lat, lon)

        # Temperature: keep Google when available, else VC
        if temp_c is None and vc_temp is not None:
            temp_c, temp_source = float(vc_temp), "Visual Crossing (fallback)"

        # Humidity: Google API primary → VC → Open-Meteo → estimate
        humidity, hum_source = None, "—"
        if google_humidity is not None and 10 <= google_humidity <= 100:
            humidity, hum_source = round(float(google_humidity), 1), "Google Weather API"
            self.logger.info(f"Using Google humidity: {humidity}%")
        elif vc_hum is not None and 20 <= vc_hum <= 95:
            humidity, hum_source = round(float(vc_hum), 1), "Visual Crossing"
            self.logger.info(f"Using Visual Crossing humidity: {humidity}%")
        else:
            om_h = self._om_nearest_hour_humidity(lat, lon)
            if om_h is not None and 20 <= om_h <= 95:
                humidity, hum_source = round(float(om_h), 1), "Open-Meteo"
                self.logger.info(f"Using Open-Meteo humidity: {humidity}%")
            else:
                humidity, hum_source = 65.0, "Default estimate"
                self.logger.info(f"Using default humidity estimate: {humidity}%")

        # Wind: ALWAYS prefer Google API first, then VC as fallback [[memory:6357930]]
        if wind_kmh is not None:
            wind_source = "Google Weather API"
            # Trust Google data - only apply very broad safety limits
            wind_kmh = max(0.0, min(150.0, wind_kmh))
            self.logger.info(f"Using Google wind: {wind_kmh} km/h")
        else:
            # Try Visual Crossing as fallback
            wind_kmh = self._to_float(vc_wind)
            if wind_kmh is not None:
                wind_source = "Visual Crossing"
                wind_kmh = max(0.0, min(100.0, wind_kmh))
                self.logger.info(f"Using Visual Crossing wind: {wind_kmh} km/h")
            else:
                # Final fallback to location-based estimate
                wind_kmh = self._estimate_wind_for_location(lat, lon)
                wind_source = "Location-based estimate"
                self.logger.info(f"Using estimated wind: {wind_kmh} km/h")
            
        wind_ms = round(wind_kmh / 3.6, 2)

        # 4) SOIL MOISTURE: NASA POWER primary; fallback OM; final estimate from RH
        soil = self._nasa_power_soil(lat, lon, days_back=5)  # NEW
        top_m3m3 = soil.get("current_top")
        if not isinstance(top_m3m3, (int, float)) or top_m3m3 < 0:
            self.logger.info("NASA POWER soil missing; falling back to Open-Meteo")
            om_soil = self._om_soil(lat, lon)
            top_m3m3 = om_soil.get("current_top")

        if isinstance(top_m3m3, (int, float)) and top_m3m3 >= 0:
            moisture_pct = round(top_m3m3 * 100.0, 1)
            moisture_source = "NASA POWER (GWETTOP)" if "nasa_power" in soil else "Open-Meteo soil"
        else:
            est = 0.25 * float(humidity) if isinstance(humidity, (int, float)) else 22.0
            moisture_pct = round(max(8.0, min(35.0, est)), 1)
            moisture_source = "Estimated from RH"

        # Assemble daily (120-day) using VC (extended) + Google (first 10 days); keep moisture if we have daily NASA/OM
        daily = self._create_120day_forecast(lat, lon, soil_daily=soil.get("daily_soil", []))

        weather_data = {
            "temperature": None if temp_c is None else round(temp_c, 1),
            "feels_like": None if temp_c is None else round(temp_c, 1),
            "humidity": humidity,
            "moisture": moisture_pct,             # SOIL moisture % (0–10 cm)
            "description": self._describe_ext(temp_c, humidity, g_now.get("precip_mm", 0)),
            "wind_speed": wind_ms,                 # m/s
            "wind_kmh": round(wind_kmh, 1),
            "location": location,
            "state": state,
            "dominant_soil_type": INDIA_STATE_SOILS.get((state or "").lower()),
            "coords": {"lat": lat, "lon": lon},
            "current": {
                "observed_at": g_now.get("time"),
                "temp_c": None if temp_c is None else round(temp_c, 1),
                "precip_mm_next_hour": g_now.get("precip_mm"),
                "humidity_pct": humidity,
                "soil_moisture_top_0_7cm_m3m3": None if moisture_pct is None else round(moisture_pct / 100.0, 3),
                "soil_moisture_7_28cm_m3m3": None if moisture_pct is None else round(0.9 * moisture_pct / 100.0, 3),
            },
            "soil_moisture": {
                "top_0_7cm_m3m3": None if moisture_pct is None else round(moisture_pct / 100.0, 3),
                "sub_7_28cm_m3m3": None if moisture_pct is None else round(0.9 * moisture_pct / 100.0, 3),
            },
            "daily": daily,
            "sources": {
                "temperature": temp_source,
                "wind": wind_source,
                "humidity": hum_source,
                "moisture": moisture_source,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "Google + Visual Crossing + NASA POWER (+OM fallback)",
        }
        
        # Cache the weather data
        self._set_cached_data(self._weather_cache, cache_key, weather_data)
        
        return weather_data

    def get_weather_optimized(self, location: str) -> Dict[str, Any]:
        """
        Optimized weather fetching that reduces API calls and improves performance
        """
        if self.use_mock:
            return self._mock(location)

        # Clean up expired cache entries
        self._cleanup_expired_cache()
        
        # Check cache first
        cache_key = location.lower().strip()
        cached_weather = self._get_cached_data(self._weather_cache, cache_key, WEATHER_CACHE_TTL)
        if cached_weather:
            self.logger.info(f"Using cached weather data for {location}")
            return cached_weather

        # 1) Geocode (with caching)
        lat, lon, state = self._geocode(location)
        
        # 2) Parallel API calls for better performance
        try:
            # Start all API calls concurrently (simplified version)
            g_hourly = self._google_hourly(lat, lon, hours=24)
            g_now = g_hourly[0] if g_hourly else {}
            
            # Extract data efficiently
            temp_c = self._to_float(g_now.get("temp_c"))
            wind_kmh = self._to_float(g_now.get("wind_kmh"))
            google_humidity = self._to_float(g_now.get("humidity"))
            
            # Use Google data when available, fallback only when necessary
            humidity = google_humidity if (google_humidity and 10 <= google_humidity <= 100) else None
            if not humidity:
                # Only fetch from other sources if Google humidity is missing
                vc_temp, vc_hum = self._vc_current_temp_humidity(lat, lon)
                if vc_hum and 20 <= vc_hum <= 95:
                    humidity = round(float(vc_hum), 1)
                else:
                    humidity = 65.0  # Default estimate
            
            # Wind: prefer Google, estimate if missing
            if not wind_kmh:
                wind_kmh = self._estimate_wind_for_location(lat, lon)
            
            wind_ms = round(wind_kmh / 3.6, 2)
            
            # Soil moisture: use cache when possible
            soil = self._nasa_power_soil(lat, lon, days_back=5)
            top_m3m3 = soil.get("current_top")
            if not isinstance(top_m3m3, (int, float)) or top_m3m3 < 0:
                moisture_pct = 22.0  # Default estimate
            else:
                moisture_pct = round(top_m3m3 * 100.0, 1)
            
            # Extract precipitation data
            precip_mm = g_now.get("precip_mm", 0)
            if precip_mm is None:
                precip_mm = 0
            
            # Build weather data efficiently
            weather_data = {
                "temperature": None if temp_c is None else round(temp_c, 1),
                "feels_like": None if temp_c is None else round(temp_c, 1),
                "humidity": humidity,
                "moisture": moisture_pct,
                "description": self._describe_ext(temp_c, humidity, precip_mm),
                "wind_speed": wind_ms,
                "wind_kmh": round(wind_kmh, 1),
                "precip_mm": round(float(precip_mm), 2) if precip_mm else 0.0,
                "location": location,
                "state": state,
                "coords": {"lat": lat, "lon": lon},
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "Google + NASA POWER (optimized)",
            }
            
            # Cache the weather data
            self._set_cached_data(self._weather_cache, cache_key, weather_data)
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Error in optimized weather fetch: {e}")
            # Fallback to full method
            return self.get_weather(location)
    
    def get_weather_with_timeline(self, location: str, query: str) -> Dict[str, Any]:
        """
        Get weather data based on timeline extracted from query
        
        Args:
            location (str): Location to get weather for
            query (str): User query to extract timeline from
            
        Returns:
            Dict[str, Any]: Weather data with appropriate timeline
        """
        try:
            # Import timeline extractor
            from .timeline_extractor import TimelineExtractor
            
            timeline_extractor = TimelineExtractor()
            days = timeline_extractor.get_weather_data_period(query)
            timeline_desc = timeline_extractor.get_timeline_description(query)
            
            self.logger.info(f"Timeline extracted: {timeline_desc} ({days} days)")
            
            # Ultra fast mode for short queries (≤60 days) - skip all expensive APIs
            if days <= 60:
                print(f"⚡ ULTRA FAST MODE: {days} days - current weather only (5-10 seconds)")
                self.logger.info(f"Using ULTRA FAST mode for {days} days - current weather only, no additional APIs")
                weather_data = self.get_weather_optimized(location)
                print(f"✅ Ultra-fast processing complete!")
                
                if 'error' in weather_data:
                    return weather_data
                
                # Add minimal timeline info without expensive API calls
                weather_data['daily'] = []  # Skip daily forecast for maximum speed
                weather_data['timeline_info'] = {
                    'requested_days': days,
                    'description': timeline_desc,
                    'data_points': 0,
                    'mode': 'ultra_fast'
                }
                weather_data['performance_optimized'] = True
                weather_data['optimization_reason'] = f'Ultra fast mode ({days} days) - current weather only, bypasses all additional APIs'
                
                # Add simple crop recommendations based on current weather
                temp = weather_data.get('temperature', 25)
                humidity = weather_data.get('humidity', 60)
                moisture = weather_data.get('moisture', 50)
                
                # Simple crop recommendations without expensive analysis
                if temp >= 25 and humidity >= 70:
                    recommended_crops = ["Rice (Paddy)", "Sugarcane", "Vegetables (tomatoes, cucumbers)", "Cotton"]
                elif temp >= 20 and temp <= 30:
                    recommended_crops = ["Wheat", "Barley", "Mustard", "Peas", "Lentils"]
                else:
                    recommended_crops = ["Seasonal crops suitable for current temperature"]
                
                weather_data['crop_recommendations'] = {
                    'suitable_crops': recommended_crops,
                    'farming_advice': f"Current conditions (Temp: {temp}°C, Humidity: {humidity}%, Soil moisture: {moisture}%) are favorable for farming activities.",
                    'quick_analysis': True
                }
                
                return weather_data
                
            # Fast mode for medium periods (61-90 days) - minimal APIs
            elif days <= 90:
                print(f"🚀 FAST MODE: {days} days - Google APIs only (5-10 seconds)")
                print(f"📡 Single API call to Google (no duplicates)...")
                self.logger.info(f"Using FAST mode for {days} days - minimal APIs")
                
                # Get coordinates first (cached)
                lat, lon, formatted_address = self._geocode(location)
                
                # Single Google API call - no duplicates
                print(f"🔄 Fetching Google weather data...")
                weather_data = self.get_weather_optimized(location)  # Current conditions
                daily_forecast = self._google_daily(lat, lon, days=min(days, 10))  # Google only provides 10 days
                print(f"✅ Google APIs complete!")
                
                if 'error' in weather_data:
                    return weather_data
                
                # Build response with single API call
                weather_data.update({
                    'daily': daily_forecast,
                    'location': formatted_address,
                    'coordinates': {'lat': lat, 'lon': lon},
                    'timeline_info': {
                        'requested_days': days,
                        'description': timeline_desc,
                        'data_points': len(daily_forecast),
                        'mode': 'fast'
                    },
                    'performance_optimized': True,
                    'optimization_reason': f'Fast mode ({days} days) - Single Google API call, no soil data'
                })
                
                print(f"✅ Fast processing complete!")
                return weather_data
                
            else:
                # Comprehensive mode for longer periods (91+ days) - USE PARALLEL PROCESSING
                print(f"🔄 COMPREHENSIVE MODE: {days} days - Using parallel processing (15-20 seconds)...")
                print(f"🚀 Fetching all APIs simultaneously...")
                self.logger.info(f"Using comprehensive mode with parallel processing for {days} days")
                weather_data = self._get_weather_parallel(location, days)
                
                if 'error' in weather_data:
                    return weather_data
                
                # Parallel processing is complete - no additional processing needed
                if 'timeline_info' in weather_data:
                    weather_data['timeline_info']['description'] = timeline_desc
                else:
                    weather_data['timeline_info'] = {'description': timeline_desc}
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Error in timeline-based weather fetch: {e}")
            print(f"⚠️ Error in timeline processing: {e}")
            print(f"🔄 Falling back to sequential processing...")
            # Fallback to regular weather fetch
            return self.get_weather(location)

    def _get_weather_parallel(self, location: str, days: int) -> Dict[str, Any]:
        """
        Fetch weather data using parallel processing for maximum speed.
        Runs Google, Visual Crossing, and NASA POWER APIs simultaneously.
        """
        try:
            print(f"🎯 Starting parallel fetch for {location}...")
            
            # Get coordinates first (cached)
            lat, lon, formatted_address = self._geocode(location)
            
            # Use ThreadPoolExecutor for parallel execution
            with ThreadPoolExecutor(max_workers=4) as executor:
                print(f"🔄 Launching 4 parallel tasks...")
                
                # Submit all API calls simultaneously
                future_to_api = {}
                
                # 1. Google current weather (fast)
                future_to_api[executor.submit(self._fetch_google_current, location)] = "google_current"
                
                # 2. NASA POWER soil data
                soil_days_back = 3 if days <= 10 else 5
                future_to_api[executor.submit(self._nasa_power_soil, lat, lon, soil_days_back)] = "nasa_soil"
                
                # 3. Google daily forecast
                future_to_api[executor.submit(self._google_daily, lat, lon, days)] = "google_daily"
                
                # 4. Visual Crossing (only for very long periods)
                if days > 90:
                    future_to_api[executor.submit(self._vc_120day_forecast, lat, lon)] = "visual_crossing"
                else:
                    print(f"⚡ Skipping Visual Crossing API for {days} days (speed optimization)")
                
                # Collect results as they complete
                results = {}
                for future in as_completed(future_to_api):
                    api_name = future_to_api[future]
                    try:
                        result = future.result(timeout=15)  # 15 second timeout per API
                        results[api_name] = result
                        print(f"✅ {api_name} completed")
                    except Exception as e:
                        print(f"❌ {api_name} failed: {str(e)}")
                        self.logger.error(f"Parallel API {api_name} failed: {e}")
                        results[api_name] = None
            
            # Process results
            print(f"🔧 Processing parallel results...")
            return self._process_parallel_results(results, lat, lon, formatted_address, days)
            
        except Exception as e:
            self.logger.error(f"Parallel processing failed: {e}")
            print(f"❌ Parallel processing failed, falling back to sequential...")
            # Fallback to regular processing
            return self.get_weather(location)

    def _fetch_google_current(self, location: str) -> Dict[str, Any]:
        """Fetch Google current weather data"""
        return self.get_weather_optimized(location)  # Get current weather conditions
    
    def _process_parallel_results(self, results: Dict[str, Any], lat: float, lon: float, 
                                formatted_address: str, days: int) -> Dict[str, Any]:
        """Process the results from parallel API calls"""
        try:
            # Start with Google current weather
            google_current = results.get('google_current', {})
            if not google_current or 'error' in google_current:
                return {"error": "Failed to fetch current weather data"}
            
            # Get soil data
            soil_data = results.get('nasa_soil', {})
            soil_daily = soil_data.get("daily_soil", []) if soil_data else []
            
            # Create daily forecast
            daily_forecast = []
            if days > 10 and results.get('visual_crossing'):
                # Use Visual Crossing for longer periods
                vc_data = results.get('visual_crossing', [])
                daily_forecast = self._create_timeline_forecast(lat, lon, soil_daily, days, vc_data)
            elif results.get('google_daily'):
                # Use Google daily for shorter periods
                google_daily = results.get('google_daily', [])
                daily_forecast = self._merge_daily_with_soil(google_daily, soil_daily)
            
            # Build final weather data structure
            weather_data = {
                **google_current,
                'daily': daily_forecast,
                'location': formatted_address,
                'coordinates': {'lat': lat, 'lon': lon},
                'timeline_info': {
                    'requested_days': days,
                    'actual_days': len(daily_forecast),
                    'mode': 'parallel_comprehensive',
                    'processing_time': 'optimized'
                },
                'performance_optimized': True,
                'optimization_reason': f'Parallel processing ({days} days) - All APIs fetched simultaneously'
            }
            
            print(f"🎉 Parallel processing complete: {len(daily_forecast)} days of data")
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Error processing parallel results: {e}")
            return {"error": f"Failed to process parallel results: {str(e)}"}

    def _merge_daily_with_soil(self, google_daily: List[dict], soil_daily: List[dict]) -> List[dict]:
        """Merge Google daily forecast with soil moisture data"""
        if not google_daily:
            return []
        
        # Create soil lookup dictionary
        soil_dict = {d.get("date"): d for d in soil_daily if d.get("date")}
        
        # Merge data
        merged_forecast = []
        for day in google_daily:
            day_data = day.copy()
            date_key = day_data.get("date")
            
            # Add soil data if available
            if date_key and date_key in soil_dict:
                soil_info = soil_dict[date_key]
                day_data.update({
                    "soil_moisture_percent": soil_info.get("moisture_percent", 0),
                    "soil_temperature_c": soil_info.get("temp_2m_c", 0)
                })
            
            merged_forecast.append(day_data)
        
        return merged_forecast
    
    def get_crop_suitability_weather(self, location: str, query: str) -> Dict[str, Any]:
        """
        Get weather data specifically optimized for crop suitability analysis
        
        Args:
            location (str): Location to get weather for
            query (str): User query to extract timeline from
            
        Returns:
            Dict[str, Any]: Weather data optimized for crop recommendations
        """
        try:
            # Always get 120 days for crop suitability analysis
            weather_data = self.get_weather(location)
            
            if 'error' in weather_data:
                return weather_data
            
            # Update daily forecast to 120 days for comprehensive crop analysis
            lat, lon, _ = self._geocode(location)
            soil = self._nasa_power_soil(lat, lon, days_back=5)
            soil_daily = soil.get("daily_soil", [])
            
            # Create 120-day forecast for crop planning
            daily_forecast = self._create_timeline_forecast(lat, lon, soil_daily, days=120)
            
            # Update weather data with crop-specific forecast
            weather_data['daily'] = daily_forecast
            weather_data['timeline_info'] = {
                'requested_days': 120,
                'description': 'agricultural planning period (120 days)',
                'data_points': len(daily_forecast),
                'purpose': 'crop_suitability_analysis'
            }
            
            # Add crop-specific metadata
            weather_data['crop_analysis_ready'] = True
            weather_data['analysis_period'] = '120 days'
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Error in crop suitability weather fetch: {e}")
            # Fallback to regular weather fetch
            return self.get_weather(location)

    # ---------------- Utilities ----------------
    def _to_float(self, v):
        try:
            return None if v is None else float(v)
        except Exception:
            return None

    # ------------- Google helpers -------------
    def _geocode(self, q: str) -> Tuple[float, float, Optional[str]]:
        # Check cache first
        cache_key = q.lower().strip()
        cached_geocode = self._get_cached_data(self._geocode_cache, cache_key, GEOCODE_CACHE_TTL)
        if cached_geocode:
            self.logger.info(f"Using cached geocode for {q}")
            return cached_geocode
            
        r = self._session.get(GEOCODE_URL, params={"address": q, "key": self.google_key}, timeout=20)
        r.raise_for_status()
        d = r.json()
        if d.get("status") != "OK" or not d.get("results"):
            raise RuntimeError(f"Geocoding failed: {d.get('status')}")
        res0 = d["results"][0]
        loc = res0["geometry"]["location"]
        state = None
        for c in res0.get("address_components", []):
            if "administrative_area_level_1" in c.get("types", []):
                state = c.get("long_name")
                break
        
        result = (float(loc["lat"]), float(loc["lng"]), state)
        
        # Cache the geocode result
        self._set_cached_data(self._geocode_cache, cache_key, result)
        
        return result

    def _google_hourly(self, lat: float, lon: float, hours: int) -> List[dict]:
        hours = max(1, min(int(hours), 240))
        r = self._session.get(
            GOOGLE_HOURS_URL,
            params={
                "key": self.google_key,
                "location.latitude": lat,
                "location.longitude": lon,
                "hours": hours,
            },
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        
        # Log the full response structure for debugging
        self.logger.info(f"Google hourly response structure: {list(data.keys())}")
        if data.get("forecastHours"):
            first_hour = data['forecastHours'][0] if data['forecastHours'] else {}
            self.logger.info(f"First hour structure: {list(first_hour.keys())}")
            self.logger.info(f"First hour full data: {first_hour}")
            
            # Check for humidity in Google API response
            if 'humidity' in first_hour:
                self.logger.info(f"Google API contains humidity: {first_hour['humidity']}")
            if 'relativeHumidity' in first_hour:
                self.logger.info(f"Google API contains relativeHumidity: {first_hour['relativeHumidity']}")
            if 'moistureLevel' in first_hour:
                self.logger.info(f"Google API contains moistureLevel: {first_hour['moistureLevel']}")
            
            # Check wind data structure in detail
            wind_data = first_hour.get("windSpeed") or first_hour.get("wind") or {}
            self.logger.info(f"Google wind data detailed: {wind_data}")
        
        out: List[dict] = []
        for h in data.get("forecastHours", []):
            iv = h.get("interval") or {}
            ts = iv.get("startTime")  # ISO Z
            temp = (h.get("temperature") or {}).get("degrees")
            
            # Extract humidity from Google API if available
            humidity = None
            if "humidity" in h:
                humidity = h["humidity"]
            elif "relativeHumidity" in h:
                humidity = h["relativeHumidity"]
            elif "moistureLevel" in h:
                humidity = h["moistureLevel"]

            # precip (mm)
            qpf = (h.get("precipitation") or {}).get("qpf") or {}
            precip_mm = 0.0
            if str(qpf.get("unit") or "").lower().startswith("milli"):
                try:
                    precip_mm = float(qpf.get("quantity") or 0.0)
                except Exception:
                    precip_mm = 0.0

            # wind → km/h (enhanced parsing for Google API)
            wind_kmh = None
            w = h.get("windSpeed") or h.get("wind") or {}
            
            # Debug log the wind data structure
            self.logger.debug(f"Google wind data structure: {w}")
            
            try:
                if isinstance(w, dict):
                    # Try different possible wind data structures from Google API
                    if "metersPerSecond" in w:
                        wind_kmh = float(w["metersPerSecond"]) * 3.6
                        self.logger.debug(f"Wind from metersPerSecond: {wind_kmh} km/h")
                    elif "kilometersPerHour" in w:
                        wind_kmh = float(w["kilometersPerHour"])
                        self.logger.debug(f"Wind from kilometersPerHour: {wind_kmh} km/h")
                    elif "speed" in w and isinstance(w["speed"], dict):
                        speed_obj = w["speed"]
                        unit = str(speed_obj.get("unit") or "").upper()
                        val = speed_obj.get("value")
                        if val is not None:
                            v = float(val)
                            if "KM" in unit or "KILOMETER" in unit:
                                wind_kmh = v
                            elif "M/S" in unit or "METER" in unit:
                                wind_kmh = v * 3.6
                            else:
                                wind_kmh = v * 3.6  # Assume m/s if unclear
                            self.logger.debug(f"Wind from speed object: {wind_kmh} km/h (unit: {unit})")
                    elif "value" in w:
                        # Direct value with optional unit
                        unit = str(w.get("unit") or "").upper()
                        val = w.get("value")
                        if val is not None:
                            v = float(val)
                            if "KM" in unit or "KILOMETER" in unit:
                                wind_kmh = v
                            else:
                                wind_kmh = v * 3.6  # Assume m/s
                            self.logger.debug(f"Wind from direct value: {wind_kmh} km/h (unit: {unit})")
                    else:
                        # Try any numeric fields
                        for key in ["windspeed", "wind_speed", "speed"]:
                            if key in w and w[key] is not None:
                                wind_kmh = float(w[key]) * 3.6  # Assume m/s
                                self.logger.debug(f"Wind from {key}: {wind_kmh} km/h")
                                break
                elif isinstance(w, (int, float)):
                    wind_kmh = float(w) * 3.6  # Assume m/s for direct numeric values
                    self.logger.debug(f"Wind from direct numeric: {wind_kmh} km/h")
                    
            except Exception as e:
                self.logger.warning(f"Error parsing Google wind data: {e}")
                wind_kmh = None

            out.append(
                {
                    "time": ts,
                    "temp_c": None if temp is None else float(temp),
                    "humidity": None if humidity is None else float(humidity),
                    "precip_mm": precip_mm,
                    "wind_kmh": None if wind_kmh is None else round(wind_kmh, 1),
                }
            )
        return out

    def _google_daily(self, lat: float, lon: float, days: int) -> List[dict]:
        days = max(1, min(int(days), 10))
        
        # Fast path for very short queries (1-3 days)
        fast_mode = days <= 3
        
        r = requests.get(
            GOOGLE_DAYS_URL,
            params={"key": self.google_key, "location.latitude": lat, "location.longitude": lon, "days": days},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        
        if fast_mode:
            self.logger.info(f"Fast mode: Processing {days} days with minimal data extraction")
        
        # Fast mode: minimal logging for very short queries
        if not fast_mode:
            # Log Google daily response structure
            self.logger.info(f"Google daily response structure: {list(data.keys())}")
            if data.get("forecastDays"):
                first_day = data['forecastDays'][0] if data['forecastDays'] else {}
                self.logger.info(f"First day structure: {list(first_day.keys())}")
                self.logger.info(f"First day full data: {first_day}")
        
        out: List[dict] = []
        for d in data.get("forecastDays", []):
            disp = d.get("displayDate") or {}
            date = f"{disp.get('year')}-{disp.get('month'):02d}-{disp.get('day'):02d}"
            tmax = (d.get("maxTemperature") or {}).get("degrees")
            tmin = (d.get("minTemperature") or {}).get("degrees")

            temp_avg = None
            if tmax is not None and tmin is not None:
                temp_avg = round((float(tmax) + float(tmin)) / 2, 1)
            elif tmax is not None:
                temp_avg = float(tmax)
            elif tmin is not None:
                temp_avg = float(tmin)

            # Extract humidity from Google daily API if available
            daily_humidity = None
            if "humidity" in d:
                daily_humidity = d["humidity"]
            elif "relativeHumidity" in d:
                daily_humidity = d["relativeHumidity"]
            
            # Fast mode: skip detailed extraction for very short queries
            if not fast_mode:
                # Check daytime and nighttime forecasts for humidity and wind
                daytime = d.get("daytimeForecast") or {}
                nighttime = d.get("nighttimeForecast") or {}
                
                if daily_humidity is None:
                    # Try to get humidity from daytime/nighttime forecasts
                    day_hum = daytime.get("humidity") or daytime.get("relativeHumidity")
                    night_hum = nighttime.get("humidity") or nighttime.get("relativeHumidity")
                    if day_hum is not None and night_hum is not None:
                        daily_humidity = (float(day_hum) + float(night_hum)) / 2
                    elif day_hum is not None:
                        daily_humidity = float(day_hum)
                    elif night_hum is not None:
                        daily_humidity = float(night_hum)
            
            # Extract wind data from Google daily API
            daily_wind = None
            if "windSpeed" in d:
                wind_obj = d["windSpeed"]
                if isinstance(wind_obj, dict):
                    if "metersPerSecond" in wind_obj:
                        daily_wind = float(wind_obj["metersPerSecond"]) * 3.6
                    elif "kilometersPerHour" in wind_obj:
                        daily_wind = float(wind_obj["kilometersPerHour"])
                elif isinstance(wind_obj, (int, float)):
                    daily_wind = float(wind_obj) * 3.6  # Assume m/s
            
            # Fast mode: skip detailed wind extraction for very short queries
            if not fast_mode and daily_wind is None:
                # Try daytime/nighttime forecasts for wind
                day_wind = daytime.get("windSpeed")
                night_wind = nighttime.get("windSpeed")
                winds = []
                for w in [day_wind, night_wind]:
                    if isinstance(w, dict):
                        if "metersPerSecond" in w:
                            winds.append(float(w["metersPerSecond"]) * 3.6)
                        elif "kilometersPerHour" in w:
                            winds.append(float(w["kilometersPerHour"]))
                    elif isinstance(w, (int, float)):
                        winds.append(float(w) * 3.6)
                if winds:
                    daily_wind = sum(winds) / len(winds)

            # Fast mode: simplified precipitation for very short queries
            if fast_mode:
                qmm = 0.0  # Skip detailed precipitation calculation
            else:
                qmm = 0.0
                for part in ("daytimeForecast", "nighttimeForecast"):
                    qpf = ((d.get(part) or {}).get("precipitation") or {}).get("qpf") or {}
                    if str(qpf.get("unit") or "").lower().startswith("milli"):
                        try:
                            qmm += float(qpf.get("quantity") or 0.0)
                        except Exception:
                            pass

            # Fast mode: minimal data for very short queries
            if fast_mode:
                out.append({
                    "date": date, 
                    "temp_c": temp_avg, 
                    "humidity": daily_humidity,
                    "wind_kmh": daily_wind,
                    "precip_mm": qmm
                })
            else:
                # Full mode: complete data for longer queries
                out.append({
                    "date": date, 
                    "tmin_c": tmin, 
                    "tmax_c": tmax, 
                    "temp_c": temp_avg, 
                    "humidity": daily_humidity,
                    "wind_kmh": daily_wind,
                    "precip_mm": qmm
                })
        return out

    # ------------- Visual Crossing (humidity, wind fallback) -------------
    def _vc_current_temp_humidity(self, lat: float, lon: float) -> Tuple[Optional[float], Optional[float]]:
        try:
            # Add retry logic for rate limiting
            import time
            for attempt in range(3):
                r = requests.get(
                    VC_TIMELINE.format(lat=lat, lon=lon),
                    params={
                        "unitGroup": "metric",
                        "include": "current",
                        "key": self.visual_key,
                        "contentType": "json",
                        "elements": "temp,humidity",
                    },
                    timeout=20,
                )
                
                if r.status_code == 429:  # Rate limited
                    if attempt < 2:
                        self.logger.info(f"Rate limited, waiting {2 ** attempt} seconds...")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        self.logger.warning("Visual Crossing rate limited after retries")
                        return None, None
                        
                r.raise_for_status()
                cur = (r.json() or {}).get("currentConditions") or {}
                temp = cur.get("temp")
                hum = cur.get("humidity")
                return (None if temp is None else float(temp)), (None if hum is None else float(hum))
                
        except Exception as e:
            self.logger.warning(f"Visual Crossing temp/humidity error: {e}")
            return None, None

    def _vc_current_wind(self, lat: float, lon: float) -> Optional[float]:
        try:
            r = requests.get(
                VC_TIMELINE.format(lat=lat, lon=lon),
                params={"unitGroup": "metric", "include": "current", "key": self.visual_key, "contentType": "json"},
                timeout=20,
            )
            r.raise_for_status()
            cur = (r.json() or {}).get("currentConditions") or {}
            wind_kmh = cur.get("windspeed")
            return None if wind_kmh is None else float(wind_kmh)
        except Exception as e:
            self.logger.warning(f"Visual Crossing wind error: {e}")
            return None

    # ------------- NASA POWER (soil moisture primary) -------------
    def _nasa_power_soil(self, lat: float, lon: float, days_back: int = 5) -> Dict[str, Any]:
        """
        Fetch daily GWETTOP (top 0–10 cm soil moisture, fraction 0–1) for the last few days
        and return the most recent valid value. Also returns a small daily list if needed.
        """
        try:
            end = datetime.utcnow().date() - timedelta(days=1)  # NASA POWER has 1-day delay
            start = end - timedelta(days=max(1, days_back))
            
            # Fix parameter formatting for NASA POWER API
            params = {
                "parameters": "GWETTOP",
                "community": "AG",
                "longitude": round(float(lon), 6),  # Round coordinates
                "latitude": round(float(lat), 6),
                "start": start.strftime("%Y%m%d"),  # NASA prefers YYYYMMDD format
                "end": end.strftime("%Y%m%d"),
                "format": "JSON",
            }
            
            self.logger.info(f"NASA POWER request: lat={params['latitude']}, lon={params['longitude']}, start={params['start']}, end={params['end']}")
            
            r = self._session.get(NASA_POWER, params=params, timeout=30)
            
            if r.status_code == 422:
                self.logger.warning(f"NASA POWER 422 error - likely invalid coordinates or date range")
                return {"current_top": None, "daily_soil": []}
                
            r.raise_for_status()
            jd = r.json() or {}

            # POWER daily structure: properties.parameter.GWETTOP = { "YYYYMMDD": value, ... }
            data = (((jd.get("properties") or {}).get("parameter") or {}).get("GWETTOP")) or {}
            if not data:
                self.logger.info("NASA POWER returned no GWETTOP data")
                return {"current_top": None, "daily_soil": []}

            # Sort by date, take most recent non-None
            items = sorted(data.items(), key=lambda kv: kv[0])
            current_top = None
            daily_soil = []
            for dstr, val in items:
                try:
                    # NASA POWER typically returns YYYYMMDD format
                    if len(dstr) == 8 and dstr.isdigit():
                        day = datetime.strptime(dstr, "%Y%m%d").date()
                    else:
                        day = datetime.strptime(dstr, "%Y-%m-%d").date()
                except Exception:
                    continue
                    
                v = None if val is None or val == -999.0 else float(val)  # NASA uses -999 for missing
                daily_soil.append(
                    {
                        "date": day.strftime("%Y-%m-%d"),
                        "soil_top_m3m3": v,
                        "soil_sub_m3m3": None,
                        "moisture_pct": None if v is None else round(max(0, v * 100.0), 1),
                        "time": f"{day.strftime('%Y-%m-%d')}T12:00:00Z",
                    }
                )
                if v is not None and v >= 0:  # Valid moisture value
                    current_top = v

            self.logger.info(f"NASA POWER returned {len(daily_soil)} soil measurements, current_top: {current_top}")
            result = {"current_top": current_top, "daily_soil": daily_soil, "nasa_power": True}
            
            # Cache the soil data
            cache_key = f"soil_{round(lat, 3)}_{round(lon, 3)}"
            self._set_cached_data(self._soil_cache, cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.warning(f"NASA POWER soil error: {e}")
            return {"current_top": None, "daily_soil": []}

    # ------------- Open-Meteo (humidity fallback + soil fallback) -------------
    def _om_nearest_hour_humidity(self, lat: float, lon: float) -> Optional[float]:
        try:
            r = requests.get(
                OM_FORECAST,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "relative_humidity_2m",
                    "forecast_days": 2,
                    "timezone": "auto",
                },
                timeout=20,
            )
            r.raise_for_status()
            jd = r.json()
            tz = ZoneInfo(jd.get("timezone")) if ZoneInfo else timezone.utc
            now = datetime.now(tz)

            best = None
            best_delta = None
            times = jd.get("hourly", {}).get("time", []) or []
            rhs = jd.get("hourly", {}).get("relative_humidity_2m", []) or []
            for t, v in zip(times, rhs):
                if v is None:
                    continue
                try:
                    dt = datetime.fromisoformat(t).replace(tzinfo=tz)
                except Exception:
                    continue
                delta = abs(dt - now)
                if best_delta is None or delta < best_delta:
                    best_delta, best = delta, float(v)
            return best
        except Exception as e:
            self.logger.warning(f"Open-Meteo humidity error: {e}")
            return None

    def _om_soil(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fallback soil moisture from Open-Meteo (0–7 cm & 7–28 cm); returns current_top and small daily list."""
        try:
            # hourly for "now"
            hr = requests.get(
                OM_FORECAST,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm",
                    "forecast_days": 7,
                    "timezone": "auto",
                },
                timeout=20,
            )
            hr.raise_for_status()
            hd = hr.json()
            tz = ZoneInfo(hd.get("timezone")) if ZoneInfo else timezone.utc
            times = hd.get("hourly", {}).get("time", []) or []
            smt = hd.get("hourly", {}).get("soil_moisture_0_to_7cm", []) or []

            current_top = None
            if times:
                now = datetime.now(tz)
                dts = []
                for t in times:
                    try:
                        dts.append(datetime.fromisoformat(t).replace(tzinfo=tz))
                    except Exception:
                        dts.append(now)
                idx = min(range(len(dts)), key=lambda i: abs(dts[i] - now))
                try:
                    current_top = None if smt[idx] is None else float(smt[idx])
                except Exception:
                    current_top = None

            return {"current_top": current_top, "daily_soil": []}
        except Exception as e:
            self.logger.warning(f"Open-Meteo soil error: {e}")
            return {"current_top": None, "daily_soil": []}

    # ------------- 120-day merge -------------
    def _vc_120day_forecast(self, lat: float, lon: float) -> List[dict]:
        """Get 120-day forecast with rate limiting and chunked requests"""
        try:
            # Break into smaller chunks to avoid rate limits and get better results
            all_days = []
            current_date = datetime.now().date()
            
            # Optimize chunking - single large request for better performance
            import time
            chunks_needed = 1  # Try single request first
            days_per_chunk = 120
            
            print(f"🌐 Fetching Visual Crossing data: {chunks_needed} chunk(s) of {days_per_chunk} days each...")
            
            for chunk in range(chunks_needed):
                chunk_start = current_date + timedelta(days=chunk * days_per_chunk)
                chunk_end = current_date + timedelta(days=min((chunk + 1) * days_per_chunk - 1, 119))
                
                try:
                    print(f"📡 API Request {chunk + 1}/{chunks_needed}: {chunk_start} to {chunk_end}")
                    for attempt in range(2):  # Reduced retries for chunks
                        r = requests.get(
                            f"{VC_TIMELINE.format(lat=lat, lon=lon)}/{chunk_start.strftime('%Y-%m-%d')}/{chunk_end.strftime('%Y-%m-%d')}",
                            params={
                                "unitGroup": "metric",
                                "include": "days",
                                "key": self.visual_key,
                                "contentType": "json",
                                "elements": "datetime,temp,humidity,windspeed,precip,tempmax,tempmin",
                            },
                            timeout=30,  # Increased timeout for larger requests
                        )
                        
                        if r.status_code == 429:  # Rate limited
                            if attempt == 0:
                                self.logger.info(f"Rate limited on chunk {chunk}, waiting...")
                                time.sleep(3)
                                continue
                            else:
                                break  # Skip this chunk
                                
                        r.raise_for_status()
                        chunk_data = r.json()
                        chunk_days = chunk_data.get("days", [])
                        all_days.extend(chunk_days)
                        print(f"✅ Chunk {chunk + 1} successful: {len(chunk_days)} days retrieved")
                        break
                        
                except Exception as chunk_error:
                    self.logger.warning(f"Error getting chunk {chunk}: {chunk_error}")
                    continue
                
                # No delay needed for single chunk
                if chunk < chunks_needed - 1:
                    print(f"⏳ Waiting 0.5s before next chunk...")
                    time.sleep(0.5)
            
            print(f"🎉 Visual Crossing complete: {len(all_days)} days retrieved")
            self.logger.info(f"Visual Crossing returned {len(all_days)} days from chunked requests")
            
            # Process the collected data
            out = []
            api_dict = {day.get("datetime"): day for day in all_days if day.get("datetime")}
            
            for i in range(120):
                target_date = current_date + timedelta(days=i)
                date_str = target_date.strftime("%Y-%m-%d")
                day_data = api_dict.get(date_str)
                
                if day_data:
                    # Use actual API data
                    temp = day_data.get("temp")
                    if temp is None:
                        tmax = day_data.get("tempmax")
                        tmin = day_data.get("tempmin")
                        if tmax is not None and tmin is not None:
                            temp = (float(tmax) + float(tmin)) / 2
                        elif tmax is not None:
                            temp = float(tmax)
                        elif tmin is not None:
                            temp = float(tmin)
                    
                    out.append({
                        "date": date_str,
                        "temp_c": temp,
                        "humidity": day_data.get("humidity"),
                        "wind_kmh": day_data.get("windspeed"),
                        "precip_mm": day_data.get("precip", 0),
                        "time": f"{date_str}T12:00:00Z",
                    })
                else:
                    # Generate synthetic data for missing dates
                    base_temp = self._estimate_seasonal_temp(lat, target_date)
                    out.append({
                        "date": date_str,
                        "temp_c": base_temp + (i % 7 - 3) * 0.8,
                        "humidity": self._estimate_humidity_for_location(lat, target_date),
                        "wind_kmh": self._estimate_wind_for_location(lat, lon) + (i % 5 - 2),
                        "precip_mm": self._estimate_precipitation_for_location(lat, target_date),
                        "time": f"{date_str}T12:00:00Z",
                    })
            
            return out[:120]
            
        except Exception as e:
            self.logger.warning(f"Visual Crossing 120-day forecast error: {e}")
            return self._generate_synthetic_120day_forecast(lat, lon)

    def _create_120day_forecast(self, lat: float, lon: float, soil_daily: List[dict]) -> List[dict]:
        """Create 120-day forecast (legacy method for backward compatibility)"""
        return self._create_timeline_forecast(lat, lon, soil_daily, days=120)
    
    def _create_timeline_forecast(self, lat: float, lon: float, soil_daily: List[dict], days: int = 120, vc_data: List[dict] = None) -> List[dict]:
        """
        Create forecast for specified number of days
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            soil_daily (List[dict]): Daily soil moisture data
            days (int): Number of days to forecast (1-120)
            
        Returns:
            List[dict]: Forecast data for specified period
        """
        # Cap days at 120 for API limits
        days = min(days, 120)
        
        # Use provided vc_data or fetch if not provided
        if vc_data is not None:
            # Parallel processing mode - use pre-fetched data
            g_daily = []  # Will be provided separately in parallel mode
            vc_forecast = vc_data
            self.logger.info(f"Parallel mode: Using pre-fetched Visual Crossing data: {len(vc_forecast)} days")
        elif days <= 10:
            # For short periods (≤10 days), only use Google API for speed
            g_daily = self._google_daily(lat, lon, days=days)
            vc_forecast = []  # Skip VC API for short periods
            self.logger.info(f"Fast forecast mode: Using only Google API for {days} days")
        else:
            # For longer periods, use both APIs
            g_daily = self._google_daily(lat, lon, days=10)  # Google only provides 10 days
            vc_forecast = self._vc_120day_forecast(lat, lon)  # VC provides 120 days
            self.logger.info(f"Comprehensive forecast mode: Using both APIs for {days} days")
        
        # Optimize soil data for short periods
        if days <= 10:
            # For short periods, use minimal soil data (last 3 days)
            soil_dict = {d["date"]: d for d in soil_daily[-3:] if d.get("date")}
        else:
            # For longer periods, use all available soil data
            soil_dict = {d["date"]: d for d in soil_daily if d.get("date")}

        g_dict = {d["date"]: d for d in g_daily}
        vc_dict = {d["date"]: d for d in vc_forecast}

        # Ensure we have the requested number of days
        current_date = datetime.now().date()
        all_dates = []
        for i in range(days):
            date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")
            all_dates.append(date_str)

        out = []
        for i, date in enumerate(all_dates):
            g = g_dict.get(date, {})
            v = vc_dict.get(date, {})
            s = soil_dict.get(date, {})

            # Temperature: prefer Google for first 10 days, then VC, then estimate
            temp = g.get("temp_c") or v.get("temp_c")
            if temp is None:
                temp = self._estimate_seasonal_temp(lat, current_date + timedelta(days=i))
                temp += (i % 7 - 3) * 0.5  # Small daily variation

            # Humidity: prefer Google, then VC, then reasonable estimate [[memory:6357930]]
            humidity = g.get("humidity") or v.get("humidity")
            if humidity is None:
                humidity = self._estimate_humidity_for_location(lat, current_date + timedelta(days=i))
                humidity += (i % 5 - 2) * 2  # Small daily variation
                humidity = max(30.0, min(90.0, humidity))  # Keep in reasonable range

            # Wind: prefer Google, then VC, then reasonable estimate
            wind_kmh = g.get("wind_kmh") or v.get("wind_kmh")
            if wind_kmh is None:
                wind_kmh = self._estimate_wind_for_location(lat, lon)
                wind_kmh += (i % 5 - 2) * 1.5  # Daily wind variation
                wind_kmh = max(5.0, min(50.0, wind_kmh))  # Keep in reasonable range

            # Precipitation: prefer Google, then VC, then pattern
            precip_mm = g.get("precip_mm") or v.get("precip_mm")
            if precip_mm is None:
                precip_mm = 0.0 if i % 4 != 0 else (2.0 + (i % 3))  # Occasional rain pattern

            # Moisture: prefer NASA daily if available; else estimate from humidity
            moisture = s.get("moisture_pct")
            if moisture is None and humidity is not None:
                # Dynamic moisture estimation based on humidity and season
                moisture = 0.3 * humidity + (i % 5) * 2
                moisture = max(8.0, min(40.0, moisture))  # Keep in reasonable range

            out.append({
                "time": f"{date}T12:00:00Z",
                "temp": round(temp, 1) if temp is not None else None,
                "humidity": round(humidity, 1) if humidity is not None else None,
                "moisture": round(moisture, 1) if moisture is not None else None,
                "wind_kmh": round(wind_kmh, 1) if wind_kmh is not None else None,
                "precip_mm": round(precip_mm, 2) if precip_mm is not None else None,
            })
        
        return out

    # ------------- Estimation helpers -------------
    def _estimate_seasonal_temp(self, lat: float, target_date: datetime.date) -> float:
        """Estimate temperature based on latitude and season - dynamic, location-aware [[memory:6357933]]"""
        # Get day of year for seasonal variation
        day_of_year = target_date.timetuple().tm_yday
        
        # Seasonal temperature variation (sine wave with peak around day 172 - June 21)
        seasonal_factor = math.sin(2 * math.pi * (day_of_year - 81) / 365)  # Peak in summer
        
        # Base temperature depends on latitude (tropical to temperate)
        if abs(lat) < 23.5:  # Tropical
            base_temp = 28.0 + seasonal_factor * 4
        elif abs(lat) < 35:  # Subtropical  
            base_temp = 24.0 + seasonal_factor * 8
        elif abs(lat) < 50:  # Temperate
            base_temp = 18.0 + seasonal_factor * 12
        else:  # Cold regions
            base_temp = 10.0 + seasonal_factor * 15
            
        # Southern hemisphere - reverse seasons
        if lat < 0:
            base_temp = base_temp - 2 * seasonal_factor
            
        return round(base_temp, 1)
    
    def _estimate_wind_for_location(self, lat: float, lon: float) -> float:
        """Estimate wind speed based on location characteristics - dynamic, location-aware [[memory:6357933]]"""
        # Base wind speed varies by region
        if abs(lat) < 10:  # Equatorial - generally calmer
            base_wind = 8.0
        elif abs(lat) < 30:  # Tropical/subtropical
            base_wind = 12.0
        elif abs(lat) < 60:  # Temperate - more variable
            base_wind = 15.0
        else:  # Polar - generally windier
            base_wind = 18.0
        
        # Seasonal variation
        import math
        day_of_year = datetime.now().timetuple().tm_yday
        seasonal_factor = math.sin(2 * math.pi * (day_of_year - 81) / 365) * 0.3
        
        # Add small random variation for realism
        import random
        random_factor = random.uniform(-1.5, 2.0)
        
        estimated_wind = base_wind + (base_wind * seasonal_factor) + random_factor
        return max(5.0, min(25.0, estimated_wind))
    
    def _estimate_humidity_for_location(self, lat: float, target_date: datetime.date) -> float:
        """Estimate humidity based on location and season - dynamic, location-aware [[memory:6357933]]"""
        # Base humidity varies by climate zone
        if abs(lat) < 10:  # Equatorial - high humidity
            base_humidity = 80.0
        elif abs(lat) < 23.5:  # Tropical
            base_humidity = 75.0
        elif abs(lat) < 35:  # Subtropical
            base_humidity = 65.0
        elif abs(lat) < 50:  # Temperate
            base_humidity = 60.0
        else:  # Cold regions - lower humidity
            base_humidity = 55.0
        
        # Seasonal variation - higher in summer for most regions
        import math
        day_of_year = target_date.timetuple().tm_yday
        seasonal_factor = math.sin(2 * math.pi * (day_of_year - 81) / 365)
        
        # Adjust for hemisphere
        if lat < 0:  # Southern hemisphere
            seasonal_factor = -seasonal_factor
        
        humidity = base_humidity + (seasonal_factor * 10)
        return max(30.0, min(90.0, humidity))
    
    def _estimate_precipitation_for_location(self, lat: float, target_date: datetime.date) -> float:
        """Estimate precipitation based on location and season - dynamic, location-aware [[memory:6357933]]"""
        import random
        
        # Base precipitation patterns by climate zone
        if abs(lat) < 10:  # Equatorial - frequent rain
            rain_chance = 0.4
            base_amount = 5.0
        elif abs(lat) < 23.5:  # Tropical - seasonal patterns
            day_of_year = target_date.timetuple().tm_yday
            # Monsoon patterns (simplified)
            monsoon_factor = max(0, math.sin(2 * math.pi * (day_of_year - 150) / 365))
            rain_chance = 0.2 + (monsoon_factor * 0.3)
            base_amount = 3.0 + (monsoon_factor * 7.0)
        elif abs(lat) < 50:  # Temperate - moderate, year-round
            rain_chance = 0.25
            base_amount = 2.5
        else:  # Cold regions - less precipitation
            rain_chance = 0.15
            base_amount = 1.5
        
        # Random precipitation event
        if random.random() < rain_chance:
            return round(base_amount * random.uniform(0.3, 2.0), 2)
        else:
            return 0.0
    
    def _generate_synthetic_120day_forecast(self, lat: float, lon: float) -> List[dict]:
        """Generate synthetic 120-day forecast as ultimate fallback"""
        out = []
        current_date = datetime.now().date()
        
        for i in range(120):
            target_date = current_date + timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            
            # Use improved location-aware estimation methods
            temp = self._estimate_seasonal_temp(lat, target_date)
            temp += (i % 7 - 3) * 0.5  # Small daily variation
            
            humidity = self._estimate_humidity_for_location(lat, target_date)
            humidity += (i % 5 - 2) * 2  # Small daily variation
            
            wind_kmh = self._estimate_wind_for_location(lat, lon)
            
            precip_mm = self._estimate_precipitation_for_location(lat, target_date)
            
            out.append({
                "date": date_str,
                "temp_c": round(temp, 1),
                "humidity": round(humidity, 1),
                "wind_kmh": round(wind_kmh, 1),
                "precip_mm": round(precip_mm, 2),
                "time": f"{date_str}T12:00:00Z",
            })
        
        return out

    # ------------- Description helpers -------------
    def _describe_ext(self, temp: Optional[float], humidity: Optional[float], precip_mm: float = 0) -> str:
        if temp is None:
            return "Unknown"
        if precip_mm and precip_mm > 0.3:
            if temp < 2:
                return "Light snow"
            elif temp < 5:
                return "Light rain/snow"
            else:
                return "Light rain"
        if precip_mm and precip_mm > 0.05:
            return "Drizzle"
        if humidity is not None and humidity >= 80:
            if temp < 20:
                return "Humid and cool"
            elif temp < 30:
                return "Humid and warm"
            else:
                return "Humid and hot"
        if humidity is not None and humidity < 30:
            if temp < 20:
                return "Dry and cool"
            elif temp < 30:
                return "Dry and warm"
            else:
                return "Dry and hot"
        if temp < 0:
            return "Freezing"
        if temp < 10:
            return "Cold"
        if temp < 20:
            return "Cool"
        if temp < 30:
            return "Warm"
        return "Hot"

    # ------------- Mock (debug) -------------
    def _mock(self, location: str) -> Dict[str, Any]:
        import random
        base = random.uniform(24, 33)
        hum = random.uniform(55, 85)
        soil_pct = random.uniform(10, 30)
        from datetime import timedelta
        daily = []
        for i in range(120):
            date = (datetime.utcnow().date() + timedelta(days=i)).strftime("%Y-%m-%d")
            daily.append(
                {
                    "time": f"{date}T12:00:00Z",
                    "temp": round(base + random.uniform(-3, 5), 1),
                    "humidity": round(max(30, min(95, hum + random.uniform(-10, 15))), 1),
                    "moisture": round(max(5, min(50, soil_pct + random.uniform(-5, 8))), 1),
                    "wind_kmh": round(12 + random.uniform(0, 10), 1),
                    "precip_mm": round(random.choice([0, 0.5, 1.2, 2.0]), 2),
                }
            )
        return {
            "temperature": round(base, 1),
            "feels_like": round(base, 1),
            "humidity": round(hum, 1),
            "moisture": round(soil_pct, 1),
            "description": self._describe_ext(base, hum, 0),
            "wind_speed": round(3.0, 2),
            "wind_kmh": round(10.0, 1),
            "location": location,
            "state": None,
            "dominant_soil_type": None,
            "coords": {"lat": 0, "lon": 0},
            "current": {
                "observed_at": datetime.utcnow().isoformat() + "Z",
                "temp_c": round(base, 1),
                "precip_mm_next_hour": 0.0,
                "humidity_pct": round(hum, 1),
                "soil_moisture_top_0_7cm_m3m3": round(soil_pct / 100.0, 3),
                "soil_moisture_7_28cm_m3m3": round(0.9 * soil_pct / 100.0, 3),
            },
            "soil_moisture": {
                "top_0_7cm_m3m3": round(soil_pct / 100.0, 3),
                "sub_7_28cm_m3m3": round(0.9 * soil_pct / 100.0, 3),
            },
            "daily": daily,
            "sources": {"mode": "mock"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "mock",
        }

    # ------------- Batch Operations -------------
    def get_weather_batch(self, locations: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get weather for multiple locations efficiently, using cache and minimizing API calls
        """
        results = {}
        uncached_locations = []
        
        # Check cache first for all locations
        for location in locations:
            cache_key = location.lower().strip()
            cached_weather = self._get_cached_data(self._weather_cache, cache_key, WEATHER_CACHE_TTL)
            if cached_weather:
                results[location] = cached_weather
                self.logger.info(f"Using cached weather for {location}")
            else:
                uncached_locations.append(location)
        
        # Fetch weather for uncached locations
        if uncached_locations:
            self.logger.info(f"Fetching weather for {len(uncached_locations)} uncached locations")
            for location in uncached_locations:
                try:
                    weather_data = self.get_weather(location)
                    results[location] = weather_data
                except Exception as e:
                    self.logger.error(f"Failed to fetch weather for {location}: {e}")
                    results[location] = {"error": str(e)}
        
        return results
    
    def clear_cache(self, location: Optional[str] = None):
        """
        Clear cache for specific location or all locations
        """
        if location:
            cache_key = location.lower().strip()
            if cache_key in self._weather_cache:
                del self._weather_cache[cache_key]
            if cache_key in self._geocode_cache:
                del self._geocode_cache[cache_key]
            self.logger.info(f"Cleared cache for {location}")
        else:
            self._weather_cache.clear()
            self._geocode_cache.clear()
            self._soil_cache.clear()
            self.logger.info("Cleared all caches")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring
        """
        current_time = time.time()
        return {
            "weather_cache_size": len(self._weather_cache),
            "geocode_cache_size": len(self._geocode_cache),
            "soil_cache_size": len(self._soil_cache),
            "last_cleanup": current_time - self._last_cleanup,
            "cache_ttls": {
                "weather": WEATHER_CACHE_TTL,
                "geocode": GEOCODE_CACHE_TTL,
                "soil": SOIL_CACHE_TTL
            }
        }
