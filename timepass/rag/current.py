import os
import gc
import warnings
warnings.filterwarnings('ignore')

# Conservative thread settings to prevent segfaults
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1" 
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import re, unicodedata, json
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List, Tuple, Dict, Any
import time
from pathlib import Path

try:
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except:
    pass

try:
    faiss.omp_set_num_threads(1)
except:
    pass

# ==== API Key ====
# Import centralized configuration
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import config

OPENAI_KEY = config.OPENAI_API_KEY
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY

# ==== Paths ====
META_PATH = "faiss_meta.json"
INDEX_PATH = "faiss_index.idx"
CHUNKS_CSV = "faiss_chunks.csv"
EMBEDDINGS_PATH = "embeddings.npy"
WEATHER_DATA_PATH = "weather_data_cache.json"

# ==== Configuration ====
MAX_CHUNKS = config.MAX_CHUNKS
EMBEDDING_BATCH_SIZE = config.EMBEDDING_BATCH_SIZE
CHUNK_SIZE = config.CHUNK_SIZE
OVERLAP_SIZE = config.OVERLAP_SIZE

# ==== Memory-safe text processing ====
def normalize_text(text: str) -> str:
    if not text or pd.isna(text) or text == 'nan':
        return ""
    text = str(text)[:1000]
    text = re.sub(r'[^\w\s.,]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

# ==== Memory-efficient data loading ====
def load_file_safely(filepath: Path) -> pd.DataFrame:
    filename = filepath.name
    try:
        if filename.endswith(('.csv', '.csv.xls')):
            try:
                df = pd.read_csv(filepath, nrows=5000, dtype=str)
            except:
                df = pd.read_csv(filepath, dtype=str, encoding='utf-8', errors='ignore')
                if len(df) > 5000:
                    df = df.sample(n=5000, random_state=42)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath, engine='openpyxl', dtype=str, nrows=5000)
        elif filename.endswith('.xls'):
            df = pd.read_excel(filepath, engine='xlrd', dtype=str, nrows=5000)
        elif filename.endswith('.txt'):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f.readlines()[:1000] if line.strip()]
            if lines:
                df = pd.DataFrame({"text": lines})
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()
        df = df.fillna("").replace('nan', '')
        df["source_file"] = filename
        print(f" Loaded {filename} ({len(df)} rows)")
        return df
    except Exception as e:
        print(f" Could not read {filename}: {e}")
        return pd.DataFrame()

def load_weather_data_from_backend():
    """Load weather data from backend weather service"""
    try:
        import sys
        import os
        # Add parent directory to path to import weather service
        parent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_dir))
        
        from src.weather_service import WeatherService
        
        # Initialize weather service
        weather_service = WeatherService()
        
        # Get weather data for a default location (can be extended for multiple locations)
        default_locations = ["Delhi, India", "Mumbai, India", "Bangalore, India", "Chennai, India", "Hyderabad, India"]
        
        all_weather_data = []
        
        for location in default_locations:
            try:
                print(f" Fetching weather data for {location}...")
                weather_data = weather_service.get_weather(location)
                
                if weather_data and not weather_data.get('error'):
                    all_weather_data.append({
                        'location': location,
                        'data': weather_data,
                        'timestamp': weather_data.get('timestamp', time.time())
                    })
                    print(f" ✓ Weather data loaded for {location}")
                else:
                    print(f" ⚠ Failed to load weather data for {location}")
                    
            except Exception as e:
                print(f" ⚠ Error loading weather for {location}: {e}")
                continue
        
        # Cache the weather data
        try:
            with open(WEATHER_DATA_PATH, 'w') as f:
                json.dump(all_weather_data, f, indent=2, default=str)
            print(f" Weather data cached to {WEATHER_DATA_PATH}")
        except Exception as e:
            print(f" Warning: Could not cache weather data: {e}")
        
        return all_weather_data
        
    except Exception as e:
        print(f" Error loading weather data from backend: {e}")
        return []

def load_cached_weather_data():
    """Load weather data from cache if available"""
    try:
        if os.path.exists(WEATHER_DATA_PATH):
            with open(WEATHER_DATA_PATH, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is recent (less than 1 hour old)
            cache_time = os.path.getmtime(WEATHER_DATA_PATH)
            if time.time() - cache_time < 3600:  # 1 hour
                print(f" Using cached weather data (age: {int((time.time() - cache_time)/60)} minutes)")
                return cached_data
            else:
                print(f" Weather cache is stale, will fetch fresh data")
                
        return []
    except Exception as e:
        print(f" Error loading cached weather data: {e}")
        return []

def convert_weather_to_chunks(weather_data_list):
    """Convert weather data to chunks for RAG processing"""
    chunks = []
    
    for weather_entry in weather_data_list:
        location = weather_entry.get('location', 'Unknown')
        weather_data = weather_entry.get('data', {})
        
        # Current weather chunk
        current_weather = weather_data.get('current', {})
        if current_weather:
            current_chunk = f"Current weather in {location}: "
            current_chunk += f"Temperature {weather_data.get('temperature', 'N/A')}°C, "
            current_chunk += f"Feels like {weather_data.get('feels_like', 'N/A')}°C, "
            current_chunk += f"Humidity {weather_data.get('humidity', 'N/A')}, "
            current_chunk += f"Soil moisture {weather_data.get('moisture', 'N/A')}, "
            current_chunk += f"Wind speed {weather_data.get('wind_speed', 'N/A')} m/s, "
            current_chunk += f"Description: {weather_data.get('description', 'N/A')}"
            
            chunks.append({
                "text": normalize_text(current_chunk),
                "source_file": f"weather_current_{location.replace(', ', '_').replace(' ', '_')}.txt"
            })
        
        # Process 120-day forecast data
        daily_data = weather_data.get('daily', [])
        for i, day in enumerate(daily_data[:120]):  # Ensure we only take 120 days
            day_chunk = f"Weather forecast for {location} on day {i+1}: "
            day_chunk += f"Time {day.get('time', 'N/A')}, "
            day_chunk += f"Temperature {day.get('temp', 'N/A')}°C, "
            day_chunk += f"Humidity {day.get('humidity', 'N/A')}, "
            day_chunk += f"Soil moisture {day.get('moisture', 'N/A')}, "
            day_chunk += f"Wind speed {day.get('wind_kmh', 'N/A')} km/h, "
            day_chunk += f"Precipitation {day.get('precip_mm', 'N/A')} mm"
            
            # Add relative day information for easy querying
            if i == 0:
                day_chunk += " (today)"
            elif i == 1:
                day_chunk += " (tomorrow)"
            elif i < 7:
                day_chunk += f" (in {i} days)"
            elif i < 30:
                day_chunk += f" (in {i} days, week {i//7 + 1})"
            else:
                day_chunk += f" (in {i} days, month {i//30 + 1})"
            
            chunks.append({
                "text": normalize_text(day_chunk),
                "source_file": f"weather_forecast_{location.replace(', ', '_').replace(' ', '_')}_day_{i+1}.txt"
            })
        
        # Add soil type information if available
        soil_type = weather_data.get('dominant_soil_type')
        if soil_type:
            soil_chunk = f"Soil information for {location}: Dominant soil type is {soil_type}"
            chunks.append({
                "text": normalize_text(soil_chunk),
                "source_file": f"soil_info_{location.replace(', ', '_').replace(' ', '_')}.txt"
            })
    
    print(f" Converted weather data to {len(chunks)} chunks")
    return chunks

def load_all_data():
    # Look for ALL supported files in current folder
    files = []
    for ext in ["*.csv", "*.csv.xls", "*.xlsx", "*.xls", "*.txt"]:
        files.extend(Path(".").glob(ext))

    all_chunks = []
    total_loaded = 0

    # Load weather data first
    print("Loading weather data from backend...")
    weather_data = load_cached_weather_data()
    if not weather_data:
        weather_data = load_weather_data_from_backend()
    
    if weather_data:
        weather_chunks = convert_weather_to_chunks(weather_data)
        all_chunks.extend(weather_chunks)
        total_loaded += len(weather_chunks)
        print(f" Weather data loaded: {len(weather_chunks)} chunks")

    # Load file data
    for filepath in files:
        if total_loaded >= MAX_CHUNKS:
            print(f" Reached maximum chunk limit ({MAX_CHUNKS}), stopping file loading")
            break

        df = load_file_safely(filepath)
        if not df.empty:
            file_chunks = prepare_file_chunks(df)
            all_chunks.extend(file_chunks)
            total_loaded += len(file_chunks)
            del df
            gc.collect()
            print(f" Total chunks so far: {total_loaded}")

    if not all_chunks:
        raise ValueError("No valid data found.")
    if len(all_chunks) > MAX_CHUNKS:
        print(f" Limiting to {MAX_CHUNKS} chunks (was {len(all_chunks)})")
        all_chunks = all_chunks[:MAX_CHUNKS]
    return pd.DataFrame(all_chunks)


# ==== Updated: keep numeric table rows intact ====
def prepare_file_chunks(df: pd.DataFrame) -> List[dict]:
    chunks = []
    filename = df['source_file'].iloc[0] if not df.empty else "unknown"
    non_source_cols = [col for col in df.columns if col != "source_file"]
    for _, row in df.iterrows():
        if len(chunks) >= 1000:
            break
        row_parts = []
        for col in non_source_cols:
            val = str(row[col]).strip()
            if val and val != 'nan':
                row_parts.append(f"{col}: {val}")
        if row_parts:
            row_text = " | ".join(row_parts)
            normalized = normalize_text(row_text)
            if len(normalized) > 20:
                chunks.append({"text": normalized, "source_file": filename})
    return chunks

# ==== Embeddings and FAISS ====
def generate_embeddings_safely(texts: List[str], embedder: SentenceTransformer) -> np.ndarray:
    print(f"Generating embeddings for {len(texts)} texts...")
    if os.path.exists(EMBEDDINGS_PATH):
        try:
            print(" Loading cached embeddings...")
            embeddings = np.load(EMBEDDINGS_PATH)
            if embeddings.shape[0] == len(texts):
                return embeddings.astype(np.float32)
        except Exception:
            pass
    all_embeddings = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i+EMBEDDING_BATCH_SIZE]
        clean_batch = [str(t).strip()[:500] if len(str(t).strip()) > 5 else "empty text" for t in batch]
        batch_emb = embedder.encode(
            clean_batch,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=16,
            device='cpu',
            normalize_embeddings=True
        )
        all_embeddings.append(batch_emb.astype(np.float32))
        gc.collect()
    embeddings = np.vstack(all_embeddings)
    try:
        np.save(EMBEDDINGS_PATH, embeddings)
    except Exception:
        pass
    return embeddings

def build_faiss_index_safe(texts: List[str], embedder: SentenceTransformer) -> faiss.Index:
    embeddings = generate_embeddings_safely(texts, embedder)
    print("🏗️ Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    print(f"Index built with {index.ntotal} vectors")
    return index

# ==== File operations ====
def save_index(index: faiss.Index, df_chunks: pd.DataFrame, meta: dict):
    try:
        faiss.write_index(index, INDEX_PATH)
        df_chunks.to_csv(CHUNKS_CSV, index=False)
        with open(META_PATH, "w") as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        print(f"Error saving index: {e}")

def load_index():
    if all(os.path.exists(p) for p in [INDEX_PATH, CHUNKS_CSV, META_PATH]):
        try:
            index = faiss.read_index(INDEX_PATH)
            df_chunks = pd.read_csv(CHUNKS_CSV)
            with open(META_PATH) as f:
                meta = json.load(f)
            return index, df_chunks, meta
        except Exception as e:
            print(f" Error loading cached index: {e}")
    return None, None, None

# ==== Search function ====
def faiss_search(query: str, embedder: SentenceTransformer, index: faiss.Index, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    try:
        normalized_query = normalize_text(query)
        if not normalized_query:
            return np.array([]), np.array([])
        query_embedding = embedder.encode(
            [normalized_query],
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True
        ).astype(np.float32)
        distances, indices = index.search(query_embedding, min(top_k, index.ntotal))
        return indices[0], distances[0]
    except Exception as e:
        print(f" Search error: {e}")
        return np.array([]), np.array([])
# ==== Few-shot examples ====
few_shots = """
Example 1:
Context:
State | Crop | Yield
Karnataka | Wheat | 3.5
Karnataka | Rice | 4.2
Query:
Which crop has the highest yield in Karnataka?
Answer:
Rice has the highest yield in Karnataka at 4.2.

Example 2:
Context:
Crop | A2+FL
Arhar | 1200
Arhar | 1400
Arhar | 1600
Query:
What is the average A2+FL for Arhar?
Answer:
The average A2+FL for Arhar is 1400.00.

Example 3:
Context:
State | Crop | C2 | Yield
Bihar | Wheat | 3000 | 2
Punjab | Rice | 3200 | 4
Query:
Which state–crop combination offers the best cost-to-yield ratio using C2?
Answer:
Punjab Rice has the best cost-to-yield ratio with 3200 / 4 = 800.

Example 4:
Context:
Crop | State | Cost of Cultivation (C2) | Yield
Wheat | Karnataka | 20000 | 30
Rice | Karnataka | 25000 | 40
Query:
What is the total cost of cultivation in Karnataka?
Answer:
The total cost of cultivation in Karnataka is 45,000 (20,000 + 25,000).

Example 5:
Context:
State | Crop | Month | Average Yield
Punjab | Rice | July | 50
Punjab | Wheat | November | 35
Query:
What is the best time for agriculture in Punjab?
Answer:
July for Rice, which has the highest average yield of 50.

Example 6:
Context:
Crop | State | Yield
Sugarcane | Karnataka | 986.21
Sugarcane | Tamil Nadu | 1015.45
Query:
Which state has the highest sugarcane yield?
Answer:
Tamil Nadu at 1015.45.

Example 7:
Context:
Date | Precipitation
2023-07-01 | 5
2023-07-02 | 10
Query:
What was the total rainfall in the first two days of July 2023?
Answer:
15 mm (5 + 10).

Example 8:
Context:
Crop | State | Cost of Production (C2) | Yield
Wheat | Punjab | 800 | 40
Wheat | Rajasthan | 900 | 35
Query:
Which state produces wheat more cost-effectively?
Answer:
Punjab with 800/40 = 20 vs Rajasthan 900/35 ≈ 25.71, so Punjab.

Example 9:
Context:
State | Crop | Yield
Bihar | Maize | 42.95
Andhra Pradesh | Maize | 42.68
Query:
Which state grows maize with the highest yield?
Answer:
Bihar at 42.95.

Example 10:
Context:
State | Crop | A2+FL | Yield
Gujarat | Groundnut | 1500 | 20
Gujarat | Groundnut | 1700 | 22
Query:
What is the average cost-to-yield ratio (A2+FL per unit yield) for groundnut in Gujarat?
Answer:
(1500/20 + 1700/22) / 2 = (75.00 + 77.27) / 2 ≈ 76.14.

Example 11:
Context:
State | Crop | Month | Yield
Maharashtra | Cotton | August | 18
Maharashtra | Cotton | September | 22
Maharashtra | Cotton | October | 21
Query:
When should Maharashtra farmers plant cotton for best yield?
Answer:
September (highest yield 22).

Example 12:
Context:
Date | MaxT | MinT
2023-03-01 | 34 | 21
2023-03-02 | 36 | 22
2023-03-03 | 33 | 20
Query:
What was the average maximum temperature from 1–3 March 2023?
Answer:
(34 + 36 + 33) / 3 = 34.33.

Example 13:
Context:
State | Crop | C2 | Yield
Odisha | Paddy | 2600 | 38
Odisha | Paddy | 2800 | 41
Query:
What is the total yield of paddy in Odisha and average C2?
Answer:
Total yield = 79 (38 + 41); average C2 = (2600 + 2800)/2 = 2700.

Example 14:
Context:
State | Crop | Yield
Rajasthan | Bajra | 12
Rajasthan | Bajra | 14
Rajasthan | Bajra | 13
Query:
What is the median yield of bajra in Rajasthan?
Answer:
13.

Example 15:
Context:
Date | Precipitation
2023-08-10 | 0
2023-08-11 | 0
2023-08-12 | 12
2023-08-13 | 0
Query:
How many dry days (0 rainfall) were there?
Answer:
3 dry days.

Example 16:
Context:
State | Crop | A2+FL | Yield
Andhra Pradesh | Chili | 4000 | 10
Andhra Pradesh | Chili | 4500 | 12
Query:
What is the total revenue needed (A2+FL) and weighted average yield for chili in Andhra Pradesh?
Answer:
Total A2+FL = 8500; weighted average yield = (4000*10 + 4500*12) / (4000 + 4500) ≈ 11.06.

Example 17:
Context:
State | Crop | Month | Yield
Karnataka | Ragi | June | 15
Karnataka | Ragi | July | 19
Karnataka | Ragi | August | 18
Query:
Best month to sow ragi in Karnataka for highest yield?
Answer:
July (yield 19).

Example 18:
Context:
State | Crop | C2 | Yield
Tamil Nadu | Rice | 3200 | 50
Kerala | Rice | 3100 | 44
Query:
Which state is more efficient for rice (lower C2 per unit yield)?
Answer:
Tamil Nadu: 3200/50 = 64 vs Kerala: 3100/44 ≈ 70.45; Tamil Nadu is more efficient.

Example 19:
Context
YEAR |ANNUAL |JAN-FEB |MAR-MAY|JUN-SEP|OCT-DEC
1901 28.96 23.27 31.46 31.27 27.25
1902 29.22 25.75 31.76 31.09 26.49 

State |District |Date|Year |Month|Avg_rainfall|Agency_name
Kerala Kannur 2025-02-20 2025 02 0.0 NRSC VIC MODEL
Kerala Kannur 2025-02-21 2025 02 0.0200524299 NRSC VIC MODEL

Query: When should we irrigate in Kannur district in Kerala?
Answer:
The perfect time to irrigate is when the Avg_rainfall <= 3.6 and temperature <= 28. So in this case in Kannur district in Kerala it is best to irrigate in the 02 month which is February. So finally perfect time to irrigate is January - February where Avg_rainfall <= 3.6 and temperature <= 28.

Context:
Crop | State | MinTemp | MaxTemp
Paddy | Tamil Nadu | 20 | 35
Paddy | Andhra Pradesh | 22 | 34
Query:
Is it suitable to grow rice at 30 degrees?
Answer:
Yes. Rice (paddy) can be grown between 20°C and 35°C in the dataset. Since 30°C is within this range, it is suitable.

Context:
Cost of Cultivation (C2) | Cost of Production | Yield
8000 | 12000 | 20
9000 | 13500 | 22
10000 | 15000 | 24
Query:
If my cost of cultivation is 9500, what will be my cost of production and yield?
Answer:
By analyzing the trend:
- Cost of production increases by about 1500 for every +1000 in cultivation cost.
- Yield increases by about 2 for every +1000 in cultivation cost.
So for 9500, we can estimate:
Cost of production ≈ 14250
Yield ≈ 23.


Context:
Cost of Cultivation (C2) | Cost of Production | Yield
5000 | 7000 | 15
6000 | 8500 | 17
7000 | 10000 | 19
Query:
If my cost of cultivation is 8000, what will be my cost of production and yield?
Answer:
Following the trend:
- Cost of production increases by about 1500 for every +1000 in cultivation cost.
- Yield increases by about 2 for every +1000 in cultivation cost.
So for 8000, we can estimate:
Cost of production ≈ 11500
Yield ≈ 21.

Context:
Cost of Cultivation (C2) | Cost of Production | Yield
12000 | 16000 | 28
14000 | 18500 | 32
Query:
If my cost of cultivation is 13000, what will be my cost of production and yield?
Answer:
The midpoint between 12000 and 14000:
- Cost of production ≈ (16000 + 18500)/2 = 17250
- Yield ≈ (28 + 32)/2 = 30
So for 13000, estimated cost of production is 17250 and yield is 30.

Context:
Crop | Growth Days | Sowing Month | Harvest Month
Rice | 120         | June         | October
Rice | 105         | December     | March

Query: How many days does rice take to harvest?
Answer: About 120 days for Kharif season, 105 days for Rabi season rice.


Context:
State | Crop | Yield | Fertilizer Used | Irrigation | Soil Quality
Punjab | Wheat | 35 | High | Drip | Good
Punjab | Wheat | 30 | Low | Flood | Poor
Query:
How can I increase wheat yield in Punjab?
Answer:
To increase wheat yield in Punjab:
1. **Improve Fertilizer Use**: Switch from low to high-quality fertilizers for better growth.
2. **Optimize Irrigation**: Use drip irrigation instead of flood irrigation to avoid water wastage and increase soil moisture consistency.
3. **Enhance Soil Quality**: Conduct soil health tests and add organic matter to improve soil structure and fertility.
4. **Crop Variety**: Use high-yielding or drought-resistant varieties suited for the local climate.


Context:
State | Crop | Yield | Temperature | Rainfall
Karnataka | Rice | 4.5 | 30°C | 1000 mm
Karnataka | Rice | 3.5 | 32°C | 900 mm
Query:
How can I improve rice yield in Karnataka?
Answer:
To improve rice yield in Karnataka:
1. **Temperature Management**: Opt for rice varieties that are tolerant to higher temperatures (if it frequently exceeds 32°C).
2. **Water Management**: Use efficient irrigation techniques (e.g., SRI - System of Rice Intensification) to manage water and reduce irrigation needs.
3. **Soil Fertility**: Apply balanced fertilizers, including micronutrients, to support healthy growth and increase yield.
4. **Pest Control**: Monitor for pests and diseases, and use organic or chemical treatments as needed to prevent yield loss.


Context:
State | Crop | Yield | Soil Type | Irrigation
Tamil Nadu | Groundnut | 1200 | Sandy | Drip
Tamil Nadu | Groundnut | 1000 | Clay | Flood
Query:
What can be done to increase groundnut yield in Tamil Nadu?
Answer:
To increase groundnut yield in Tamil Nadu:
1. **Improve Irrigation**: For clay soils, switch from flood to drip irrigation to prevent waterlogging and ensure better root development.
2. **Soil Health**: Use organic compost to improve soil texture and enhance nutrient retention, especially for sandy soils.
3. **Fertilization**: Use a balanced mix of nitrogen, phosphorus, and potassium, along with micronutrients to enhance growth.
4. **Pest and Disease Control**: Regularly monitor for pests and treat early to prevent any damage that may reduce yields.


Context:
State | Crop | Yield | Sowing Month | Harvest Month | Temperature
Uttar Pradesh | Maize | 3.2 | March | July | 25°C
Uttar Pradesh | Maize | 2.8 | April | August | 28°C
Query:
How can I increase maize yield in Uttar Pradesh?
Answer:
To increase maize yield in Uttar Pradesh:
1. **Optimize Sowing Month**: Sowing in March (as shown in the dataset) has a higher yield. Avoid delaying sowing into April when temperatures rise.
2. **Temperature Management**: Use heat-resistant maize varieties to cope with temperatures exceeding 28°C during the growing season.
3. **Irrigation Techniques**: Implement water-saving irrigation practices (e.g., drip or sprinkler) to maintain soil moisture during peak heat periods.
4. **Soil Fertility**: Apply high-quality fertilizers and ensure the soil has adequate levels of nitrogen and other essential nutrients for maize growth.

Example 24:
Context:
Crop | Fertilizer | Yield
Barley | Urea | 32
Barley | DAP | 35
Barley | NPK | 38
Query:
What is the best fertilizer for Barley?
Answer:
The best fertilizer for Barley is NPK, as it gives the highest yield (38) compared to Urea (32) and DAP (35).

Example 25:
Context:
Weather forecast for Delhi_India on day 2: Time 2024-01-22T12:00:00Z, Temperature 18.5°C, Humidity 65.0, Soil moisture 22.3, Wind speed 12.5 km/h, Precipitation 0.0 mm (tomorrow)
Query:
What will be the weather tomorrow in Delhi?
Answer:
Tomorrow in Delhi, the weather will be: Temperature 18.5°C, Humidity 65%, Soil moisture 22.3%, Wind speed 12.5 km/h, with no precipitation expected (0.0 mm).

Example 26:
Context:
Current weather in Mumbai_India: Temperature 28.2°C, Feels like 30.1°C, Humidity 78.0, Soil moisture 35.2, Wind speed 3.2 m/s, Description: humid and warm
Weather forecast for Mumbai_India on day 1: Temperature 29.0°C, Humidity 75.0, (today)
Query:
What's the weather like today in Mumbai?
Answer:
Today in Mumbai: Current temperature is 28.2°C (feels like 30.1°C), humidity 78%, soil moisture 35.2%, wind speed 3.2 m/s. Conditions are humid and warm. Forecast shows temperature reaching 29°C with 75% humidity.

Example 27:
Context:
Weather forecast for Bangalore_India on day 3: Temperature 22.8°C, Humidity 58.0, Soil moisture 18.7, Wind speed 8.3 km/h, Precipitation 2.5 mm (in 3 days)
Weather forecast for Bangalore_India on day 4: Temperature 23.1°C, Humidity 60.0, Soil moisture 19.2, Wind speed 9.1 km/h, Precipitation 1.2 mm (in 4 days)
Query:
Will it rain in Bangalore this week?
Answer:
Yes, rain is expected in Bangalore this week. Day 3: light rain with 2.5 mm precipitation, temperature 22.8°C. Day 4: light rain with 1.2 mm precipitation, temperature 23.1°C.

Example 28:
Context:
Current weather in Hyderabad_India: Temperature 24.1°C, Humidity 90.0%, Soil moisture 75.0%
Crop data: Cotton - Temperature range 21-30°C, Humidity tolerance high, Water requirement moderate
Rice - Temperature range 20-35°C, Humidity tolerance very high, Water requirement high
Wheat - Temperature range 15-25°C, Humidity tolerance low, Water requirement moderate
Query:
What are suitable crops for current weather?
Answer:
Based on current weather in Hyderabad (24.1°C, 90% humidity, 75% soil moisture), suitable crops are:
1. Rice/Paddy - Excellent match (thrives in high humidity and moisture)
2. Cotton - Good match (suitable temperature and humidity tolerance)
3. Sugarcane - Good for high moisture conditions
Avoid wheat as it prefers lower humidity conditions.

Example 29:
Context:
Current weather in Delhi_India: Temperature 18.5°C, Humidity 45.0%, Soil moisture 35.0%
Query:
Which crops are best for current weather conditions?
Answer:
For Delhi's current conditions (18.5°C, 45% humidity, 35% soil moisture), recommended crops:
1. Wheat - Perfect temperature range and moderate moisture needs
2. Mustard - Thrives in cooler temperatures and moderate humidity
3. Barley - Well-suited for these conditions
4. Peas - Good for cooler weather and moderate moisture

Example 30:
Context:
Weather forecast for Chennai_India on day 1: Temperature 32.1°C, Humidity 82.0, Soil moisture 28.5, Wind speed 15.2 km/h, Precipitation 0.0 mm (today)
Weather forecast for Chennai_India on day 2: Temperature 33.5°C, Humidity 79.0, Soil moisture 26.8, Wind speed 17.1 km/h, Precipitation 0.0 mm (tomorrow)
Query:
Is it good weather for farming in Chennai this week?
Answer:
Chennai weather shows: Today 32.1°C with 82% humidity, tomorrow 33.5°C with 79% humidity. Soil moisture is good (28.5% today, 26.8% tomorrow). No rain expected. The high humidity and warm temperatures are suitable for tropical crops, but irrigation may be needed due to no precipitation.

Example 29:
Context:
Soil information for Delhi_India: Dominant soil type is Alluvial
Weather forecast for Delhi_India on day 1: Temperature 15.2°C, Humidity 45.0, Soil moisture 12.3, Wind speed 6.8 km/h (today)
Query:
What type of soil is in Delhi and current conditions?
Answer:
Delhi has Alluvial soil type. Current conditions: Temperature 15.2°C, Humidity 45%, Soil moisture 12.3%, Wind speed 6.8 km/h. The alluvial soil with current low moisture (12.3%) may need irrigation for optimal crop growth.

Example 30:
Context:
Weather forecast for Hyderabad_India on day 7: Temperature 26.8°C, Humidity 62.0, Soil moisture 24.1, Wind speed 11.5 km/h, Precipitation 0.5 mm (in 7 days, week 1)
Query:
What will be the weather next week in Hyderabad?
Answer:
Next week (day 7) in Hyderabad: Temperature 26.8°C, Humidity 62%, Soil moisture 24.1%, Wind speed 11.5 km/h, with light precipitation of 0.5 mm expected.

"""

# ==== RAG Service Functions ====
def process_rag_query(query: str, location: str = None, weather_data: Dict[str, Any] = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Process a query through the RAG system and return structured response with confidence
    
    Args:
        query: User query (any language)
        location: User location
        weather_data: Current weather data from weather service
        top_k: Number of top results to retrieve
    """
    # Step 1: Auto-detect language and translate to English
    english_query = query
    detected_language = "English"
    translation_confidence = 1.0
    
    try:
        # Import language detection and translation services
        import sys
        import os
        parent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_dir))
        
        from src.language_detection import LanguageDetector
        from src.translation_service import TranslationService
        
        # Detect language
        language_detector = LanguageDetector()
        lang_code, lang_confidence = language_detector.detect_language(query)
        detected_language = language_detector.get_language_name(lang_code)
        
        # Translate to English if not already English
        if lang_code != 'en':
            translation_service = TranslationService()
            translation_result = translation_service.translate_to_english(query, lang_code)
            
            if translation_result.get('translated_text'):
                english_query = translation_result['translated_text']
                translation_confidence = translation_result.get('confidence', 0.8)
            else:
                # Translation failed, use original query
                pass
            
    except Exception as e:
        # Language processing error, use original query
        pass
    
    # Step 2: Use weather data passed from API (no duplicate fetching)
    fresh_weather_data = weather_data  # Use weather data passed from API
    target_date = None
    confidence_score = 0.75  # Default confidence
    
    if location and fresh_weather_data and 'error' not in fresh_weather_data:
        # Parse date from English query for confidence scoring
        from datetime import datetime, timedelta
        import re
        
        today = datetime.now()
        query_lower = english_query.lower()
        
        if 'tomorrow' in query_lower:
            target_date = today + timedelta(days=1)
            confidence_score = 0.90
        elif 'today' in query_lower:
            target_date = today
            confidence_score = 0.95
        elif 'day' in query_lower:
            # Look for patterns like "7 days later", "in 5 days", "after 3 days"
            day_patterns = [
                r'(\d+)\s*days?\s*later',
                r'in\s*(\d+)\s*days?',
                r'after\s*(\d+)\s*days?',
                r'(\d+)\s*days?\s*from\s*now'
            ]
            for pattern in day_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    days_ahead = int(match.group(1))
                    target_date = today + timedelta(days=days_ahead)
                    confidence_score = max(0.60, 0.95 - (days_ahead * 0.05))
                    break
        
        if not target_date:
            target_date = today
            confidence_score = 0.85
        
        # For direct weather queries ONLY (not crop/agriculture questions), return immediate response
        is_direct_weather_query = (
            any(word in english_query.lower() for word in ['weather tomorrow', 'weather today', 'temperature tomorrow', 'humidity tomorrow']) or
            (any(word in english_query.lower() for word in ['weather', 'temperature']) and 
             not any(crop_word in english_query.lower() for crop_word in ['crop', 'crops', 'suitable', 'farming', 'agriculture', 'plant', 'grow', 'cultivation']))
        )
        
        if is_direct_weather_query:
            date_str = "today" if target_date.date() == today.date() else target_date.strftime('%B %d, %Y')
            if 'tomorrow' in query_lower:
                date_str = "tomorrow"
            
            return {
                "answer": f"The weather in {location} {date_str}: Temperature {fresh_weather_data.get('temperature', 'N/A')}°C, Humidity {fresh_weather_data.get('humidity', 'N/A')}%, Wind speed {fresh_weather_data.get('wind_speed', 'N/A')} m/s, Soil moisture {fresh_weather_data.get('moisture', 'N/A')}%.",
                "confidence": confidence_score,
                "source": "Live Weather Data",
                "original_query": query,
                "english_query": english_query,
                "detected_language": detected_language,
                "translation_confidence": translation_confidence,
                "location": location,
                "target_date": target_date.strftime('%Y-%m-%d'),
                "relevant_chunks": 1,
                "total_chunks_searched": 1,
                "processing_time": "< 1s",
                "model_used": "Weather Service API",
                "context_sources": ["Live Weather API"]
            }
    
    try:
        # Step 3: Initialize embedder and load/create index
        model_name = config.EMBEDDING_MODEL
        embedder = SentenceTransformer(model_name, device="cpu")
        
        # Load existing index or create new one
        index, df_chunks, meta = load_index()
        if index is None:
            df_chunks = load_all_data()
            
            texts = df_chunks["text"].tolist()
            index = build_faiss_index_safe(texts, embedder)
            meta = {"model_name": model_name, "total_chunks": len(df_chunks), "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            save_index(index, df_chunks, meta)
        
        # ALWAYS add fresh weather data to context when available (irrespective of query type)
        if fresh_weather_data and location:
            if 'error' not in str(fresh_weather_data).lower():
                weather_text = feed_weather_data_to_rag(fresh_weather_data, location)
                if weather_text and "error" not in weather_text.lower():
                    # Add weather data as a temporary chunk for this query
                    weather_chunk = {
                        'text': f"Current weather in {location}: {weather_text}",
                        'source_file': f'live_weather_{location}_{int(time.time())}',
                        'chunk_id': f'live_weather_{location}_{int(time.time())}'
                    }
                    df_chunks = pd.concat([df_chunks, pd.DataFrame([weather_chunk])], ignore_index=True)
                    print(f"✅ Weather data added to RAG context for {location}")
            else:
                print(f"⚠️ Weather data has error, not adding to RAG context: {fresh_weather_data}")
        else:
            print(f"⚠️ No weather data available for RAG processing")
        
        # Step 4: Preprocess English query (handle rice -> paddy, etc.)
        processed_query = english_query.lower().replace("rice", "paddy")
        
        # Search for relevant chunks using English query
        indices, scores = faiss_search(processed_query, embedder, index, top_k=top_k)
        
        if len(indices) == 0:
            return {
                "answer": "I couldn't find relevant information for your query. Please try rephrasing or ask about agriculture, crops, or weather.",
                "confidence": 0.0,
                "source": "RAG System - No Results",
                "query": query,
                "relevant_chunks": 0
            }
        
        # Get valid indices and filter by score threshold
        valid_indices = indices[indices < len(df_chunks)]
        if len(valid_indices) == 0:
            return {
                "answer": "I couldn't find valid information for your query. Please try a different question.",
                "confidence": 0.0,
                "source": "RAG System - Invalid Results",
                "query": query,
                "relevant_chunks": 0
            }
        
        # Filter by relevance score with location priority
        high_confidence_indices = []
        high_confidence_scores = []
        location_specific_results = []
        general_results = []
        
        for i, idx in enumerate(valid_indices[:top_k]):
            if i < len(scores) and scores[i] > 0.2:
                chunk_text = df_chunks.iloc[idx]['text'].lower()
                
                # Check if this chunk mentions the requested location
                if location and any(loc_part.lower() in chunk_text for loc_part in location.split(',')):
                    location_specific_results.append((scores[i] + 0.3, idx))  # Boost location-specific results
                else:
                    general_results.append((scores[i], idx))
        
        # Combine results: location-specific first, then general
        all_results = sorted(location_specific_results, reverse=True) + sorted(general_results, reverse=True)
        
        for score, idx in all_results[:10]:  # Take top 10 results
            high_confidence_indices.append(idx)
            high_confidence_scores.append(score)
        
        if not high_confidence_indices:
            return {
                "answer": "I found some information but it doesn't seem directly relevant to your query. Please try asking more specific questions about agriculture, weather, or crops.",
                "confidence": 0.1,
                "source": "RAG System - Low Relevance",
                "query": query,
                "relevant_chunks": len(valid_indices)
            }
        
        # Get relevant chunks
        retrieved = df_chunks.iloc[high_confidence_indices]
        context_parts = []
        for i, (_, row) in enumerate(retrieved.iterrows()):
            context_parts.append(f"- {row['text']} (source: {row['source_file']})")
        
        context = "\n".join(context_parts)
        
        # Calculate dynamic confidence based on relevance scores and data freshness
        avg_relevance = sum(high_confidence_scores) / len(high_confidence_scores)
        base_confidence = min(0.95, avg_relevance)  # Cap at 95%
        
        # Adjust confidence based on whether we have fresh weather data
        if fresh_weather_data and location:
            confidence = min(0.95, base_confidence + 0.10)  # Boost for fresh weather data
        else:
            confidence = base_confidence
            
        # Use the confidence score calculated from date parsing if available
        if 'confidence_score' in locals() and confidence_score:
            confidence = max(confidence, confidence_score)
        
        # Check if this is a simple weather query (using English query) - exclude agriculture questions
        is_simple_weather = (
            any(word in english_query.lower() for word in ['weather tomorrow', 'temperature tomorrow', 'humidity tomorrow', 'weather today', 'tomorrow weather', 'tomorrow temperature', 'tomorrow humidity']) and
            not any(crop_word in english_query.lower() for crop_word in ['crop', 'crops', 'suitable', 'farming', 'agriculture', 'plant', 'grow', 'cultivation'])
        )
        
        # Check if this is specifically asking for tomorrow's temperature only
        is_tomorrow_temp_only = any(phrase in english_query.lower() for phrase in [
            'what will be the weather tomorrow',
            'weather tomorrow',
            'temperature tomorrow', 
            'tomorrow weather',
            'tomorrow temperature'
        ]) and not any(crop_word in english_query.lower() for crop_word in ['crop', 'crops', 'suitable', 'farming', 'agriculture', 'plant', 'grow', 'cultivation'])
        
        if is_tomorrow_temp_only:
            # For tomorrow weather queries, provide only temperature forecast without farming advice
            if fresh_weather_data and 'error' not in str(fresh_weather_data).lower():
                # Get tomorrow's forecast from daily data if available
                tomorrow_temp = "N/A"
                if 'daily' in fresh_weather_data and fresh_weather_data['daily']:
                    # Look for tomorrow's data (index 1, since 0 is today)
                    if len(fresh_weather_data['daily']) > 1:
                        tomorrow_data = fresh_weather_data['daily'][1]
                        tomorrow_temp = tomorrow_data.get('temp', tomorrow_data.get('temp_c', 'N/A'))
                    elif len(fresh_weather_data['daily']) > 0:
                        # If only today's data available, use current temperature as estimate
                        tomorrow_temp = fresh_weather_data.get('temperature', 'N/A')
                else:
                    # Fallback to current temperature
                    tomorrow_temp = fresh_weather_data.get('temperature', 'N/A')
                
                # Simple template for temperature-only queries
                template = ChatPromptTemplate.from_template(f"""
Answer this weather question directly and briefly. Only provide the temperature information requested.

Question: {{query}}

Tomorrow's temperature in {location}: {tomorrow_temp}°C

Keep the response short and only mention the temperature. Do not provide farming advice or other weather details unless specifically asked.""")
            else:
                template = ChatPromptTemplate.from_template(f"""
Weather data is not available for {location} at this time. Please try again later.

Question: {{query}}""")
        elif is_simple_weather and context_parts:
            # For simple weather queries, use a direct template with location priority (ALWAYS includes weather context)
            weather_context = ""
            if fresh_weather_data and 'error' not in str(fresh_weather_data).lower():
                weather_context = f"""
**Current Weather in {location}:**
- Temperature: {fresh_weather_data.get('temperature', 'N/A')}°C
- Humidity: {fresh_weather_data.get('humidity', 'N/A')}%
- Soil Moisture: {fresh_weather_data.get('moisture', 'N/A')}%
- Wind Speed: {fresh_weather_data.get('wind_speed', 'N/A')} m/s
- Rainfall: {fresh_weather_data.get('precip_mm', 'N/A')} mm
"""
            else:
                weather_context = f"""
**Weather Data:**
No current weather data available for {location}
"""
            
            template = ChatPromptTemplate.from_template(f"""
IMPORTANT: ALWAYS start your response with current weather data for {location}:

{weather_context}

Then give a simple, direct answer for the SPECIFIC LOCATION requested.

Location requested: {location or 'Not specified'}
Original query language: {detected_language}

Context:
{{context}}

English Query: {{query}}

IMPORTANT: 
1. ALWAYS show current weather data first
2. Only use weather data that matches the requested location "{location}"
3. If no data for "{location}" is found, say "Weather data not available for {location}"
4. Keep it simple and direct

Answer format: 
**Current Weather in {location}:**
[Show current weather data]

**Forecast:**
[Answer the specific question]""")
        else:
            # Better classification of different query types
            is_crop_recommendation_query = any(phrase in english_query.lower() for phrase in [
                'suitable crops', 'crops for', 'which crops', 'best crops', 'recommend crops',
                'what crops', 'crop recommendations', 'crops suitable', 'good crops',
                'seed variety', 'seed varieties', 'what seeds', 'which seeds', 'unpredictable weather',
                'variable weather', 'changing weather', 'weather resistant', 'hardy crops',
                'resilient crops', 'adaptable crops', 'flexible crops'
            ])
            
            is_specific_crop_query = any(crop in english_query.lower() for crop in [
                'wheat', 'rice', 'corn', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane',
                'barley', 'mustard', 'peas', 'lentils', 'beans', 'cucumber', 'carrot'
            ]) and any(word in english_query.lower() for word in ['good', 'suitable', 'grow', 'plant', 'weather'])
            
            is_general_weather_query = any(phrase in english_query.lower() for phrase in [
                'how is the weather', 'weather conditions', 'current weather', 'weather forecast'
            ]) and not any(crop_word in english_query.lower() for crop_word in ['crop', 'plant', 'grow', 'farm'])
            
            is_farming_advice_query = any(phrase in english_query.lower() for phrase in [
                'farming advice', 'agricultural advice', 'when to plant', 'how to grow',
                'irrigation', 'fertilizer', 'pest control', 'harvest time'
            ])
            
            if is_crop_recommendation_query and fresh_weather_data:
                # Use concise crop recommendation template
                # Check if this is a seed variety question
                is_seed_variety_question = any(phrase in english_query.lower() for phrase in [
                    'seed variety', 'seed varieties', 'what seeds', 'which seeds', 'unpredictable weather',
                    'variable weather', 'changing weather', 'weather resistant'
                ])
                
                if is_seed_variety_question:
                    # Enhanced template for seed variety questions
                    template = ChatPromptTemplate.from_template(f"""
IMPORTANT: ALWAYS start your response with current weather data for {location}:

**Current Weather in {location}:**
- Temperature: {fresh_weather_data.get('temperature', 'N/A')}°C
- Humidity: {fresh_weather_data.get('humidity', 'N/A')}%
- Soil Moisture: {fresh_weather_data.get('moisture', 'N/A')}%
- Wind Speed: {fresh_weather_data.get('wind_speed', 'N/A')} m/s
- Rainfall: {fresh_weather_data.get('precip_mm', 'N/A')} mm

Based on these weather conditions, provide comprehensive seed variety recommendations:

**Best Seed Varieties for Current Conditions (5-7 varieties):**
1. [Crop Name + Variety] - [Why this variety is ideal for current weather]
2. [Crop Name + Variety] - [Why this variety is ideal for current weather]
3. [Crop Name + Variety] - [Why this variety is ideal for current weather]
4. [Crop Name + Variety] - [Why this variety is ideal for current weather]
5. [Crop Name + Variety] - [Why this variety is ideal for current weather]

**Seed Varieties to Avoid (3-4 varieties):**
• [Crop Name + Variety] - [Why this variety is unsuitable for current weather]
• [Crop Name + Variety] - [Why this variety is unsuitable for current weather]
• [Crop Name + Variety] - [Why this variety is unsuitable for current weather]

**Seed Selection Strategy for Unpredictable Weather:**
• **Disease-Resistant Varieties**: Essential for high humidity conditions
• **Drought-Tolerant Seeds**: Important if soil moisture varies
• **Early-Maturing Varieties**: Reduce exposure to weather changes
• **Weather-Adaptive Strains**: Handle temperature and humidity fluctuations
• **Local Climate-Adapted Seeds**: Best suited for {location} conditions

**Planting Recommendations:**
- Plant in stages to spread risk
- Start with hardy, weather-resistant varieties
- Consider crop rotation for disease prevention
- Monitor weather forecasts for optimal planting times

Context: {{context}}
Question: {{query}}""")
                else:
                    # Standard crop recommendation template
                    template = ChatPromptTemplate.from_template(f"""
IMPORTANT: ALWAYS start your response with current weather data for {location}:

**Current Weather in {location}:**
- Temperature: {fresh_weather_data.get('temperature', 'N/A')}°C
- Humidity: {fresh_weather_data.get('humidity', 'N/A')}%
- Soil Moisture: {fresh_weather_data.get('moisture', 'N/A')}%
- Wind Speed: {fresh_weather_data.get('wind_speed', 'N/A')} m/s
- Rainfall: {fresh_weather_data.get('precip_mm', 'N/A')} mm

Based on these weather conditions, provide:

**Recommended Crops (3-5 crops):**
1. [Crop Name] - [Brief reason why it's suitable for current weather]
2. [Crop Name] - [Brief reason why it's suitable for current weather]  
3. [Crop Name] - [Brief reason why it's suitable for current weather]

**Crops to Avoid (2-3 crops):**
• [Crop Name] - [Reason why it's not suitable for current weather]
• [Crop Name] - [Reason why it's not suitable for current weather]

**Key Considerations:**
- Temperature range: {fresh_weather_data.get('temperature', 'N/A')}°C is [optimal/too hot/too cold] for [crop types]
- Humidity level: {fresh_weather_data.get('humidity', 'N/A')}% is [ideal/too high/too low] for [crop types]
- Soil moisture: {fresh_weather_data.get('moisture', 'N/A')}% indicates [good drainage/water retention needed]

Keep recommendations practical and based on current weather conditions.

Context: {{context}}
Question: {{query}}""")
            elif is_specific_crop_query and fresh_weather_data:
                # Template for specific crop suitability questions
                template = ChatPromptTemplate.from_template(f"""
Answer this specific crop question directly and concisely.

**Current Weather in {location}:**
- Temperature: {fresh_weather_data.get('temperature', 'N/A')}°C
- Humidity: {fresh_weather_data.get('humidity', 'N/A')}%
- Soil Moisture: {fresh_weather_data.get('moisture', 'N/A')}%
- Wind Speed: {fresh_weather_data.get('wind_speed', 'N/A')} m/s
- Rainfall: {fresh_weather_data.get('precip_mm', 'N/A')} mm

Based on the current weather conditions above, answer the specific question about the crop mentioned.

Question: {{query}}

**Answer Format:**
1. **Direct Answer**: [YES/NO] - [Crop name] is [suitable/not suitable] for current weather
2. **Reasoning**: [Brief explanation based on temperature, humidity, and soil conditions]
3. **Alternative Crops**: If not suitable, suggest 2-3 crops that would work better
4. **Avoidance Note**: If applicable, mention what conditions this crop prefers

Be specific to the crop and weather mentioned in the question. Keep it concise but informative.

Context: {{context}}""")
            elif is_general_weather_query:
                # Template for general weather questions
                template = ChatPromptTemplate.from_template(f"""
Provide current weather information for {location}.

**Current Weather in {location}:**
- Temperature: {fresh_weather_data.get('temperature', 'N/A')}°C
- Humidity: {fresh_weather_data.get('humidity', 'N/A')}%
- Soil Moisture: {fresh_weather_data.get('moisture', 'N/A')}%
- Wind Speed: {fresh_weather_data.get('wind_speed', 'N/A')} m/s
- Rainfall: {fresh_weather_data.get('precip_mm', 'N/A')} mm
- Description: {fresh_weather_data.get('description', 'N/A')}

Answer the weather question directly based on the current conditions above.

Question: {{query}}""")
            else:
                # Use detailed template for complex queries (ALWAYS includes weather context)
                weather_context = ""
                if fresh_weather_data and 'error' not in str(fresh_weather_data).lower():
                    weather_context = f"""
**Current Weather in {location}:**
- Temperature: {fresh_weather_data.get('temperature', 'N/A')}°C
- Humidity: {fresh_weather_data.get('humidity', 'N/A')}%
- Soil Moisture: {fresh_weather_data.get('moisture', 'N/A')}%
- Wind Speed: {fresh_weather_data.get('wind_speed', 'N/A')} m/s
- Rainfall: {fresh_weather_data.get('precip_mm', 'N/A')} mm
"""
                else:
                    weather_context = f"""
**Weather Data:**
No current weather data available for {location}
"""
                
                template = ChatPromptTemplate.from_template(f"""
You are an expert Agriculture and Weather assistant. Answer the user's question directly and specifically.

{weather_context}

CRITICAL INSTRUCTIONS:
1. Read the question carefully and answer EXACTLY what is being asked
2. Do NOT provide generic farming advice unless specifically requested
3. For specific crop questions (like "is wheat good for this weather"): Give a direct YES/NO answer with brief reasoning
4. For weather questions: Provide the specific weather information requested
5. For crop recommendation questions: List suitable crops
6. Keep responses focused and relevant to the specific question

Question: {{query}}
Location: {location or 'Not specified'}

Available context: {{context}}

Answer the question directly and specifically. Do not add unnecessary information.""")

        try:
            final_prompt = template.format(context=context, query=english_query)
            llm = ChatOpenAI(model=config.OPENAI_MODEL, temperature=config.LLM_TEMPERATURE)
            response = llm.invoke(final_prompt)
            
            answer = response.content.strip()
            
            return {
                "answer": answer,
                "confidence": float(confidence),
                "source": "RAG System",
                "original_query": query,
                "english_query": english_query,
                "detected_language": detected_language,
                "translation_confidence": translation_confidence,
                "location": location,
                "relevant_chunks": int(len(high_confidence_indices)),
                "total_chunks_searched": int(len(df_chunks)),
                "processing_time": "< 3s",
                "model_used": config.OPENAI_MODEL,
                "context_sources": [str(row['source_file']) for _, row in retrieved.iterrows()]
            }
            
        except Exception as e:
            return {
                "answer": f"I found relevant information but encountered an error generating the response: {str(e)}",
                "confidence": 0.3,
                "source": "RAG System - Generation Error",
                "query": query,
                "relevant_chunks": int(len(high_confidence_indices)),
                "error": str(e)
            }
            
    except Exception as e:
        return {
            "answer": f"Error processing your query: {str(e)}",
            "confidence": 0.0,
            "source": "RAG System - Processing Error",
            "query": query,
            "error": str(e)
        }

def feed_weather_data_to_rag(weather_data: Dict[str, Any], location: str) -> str:
    """
    Feed weather data into RAG system for processing
    
    Args:
        weather_data: Weather data from weather service
        location: Location name
        
    Returns:
        Formatted weather text for RAG processing
    """
    try:
        if not weather_data or 'error' in weather_data:
            return f"Weather data unavailable for {location}"
        
        # Extract key weather information
        temp = weather_data.get('temperature', 'N/A')
        humidity = weather_data.get('humidity', 'N/A')
        description = weather_data.get('description', 'N/A')
        wind_speed = weather_data.get('wind_speed', 'N/A')
        feels_like = weather_data.get('feels_like', 'N/A')
        moisture = weather_data.get('moisture', 'N/A')
        
        # Get timeline information if available
        timeline_info = weather_data.get('timeline_info', {})
        timeline_desc = timeline_info.get('description', '120 days') if timeline_info else '120 days'
        data_points = timeline_info.get('data_points', 120) if timeline_info else 120
        mode = timeline_info.get('mode', 'comprehensive')
        
        # Ultra fast mode for short queries - skip expensive crop analysis
        if mode == 'ultra_fast' or mode == 'super_fast':
            # Get crop recommendations from weather data if available
            crop_recs = weather_data.get('crop_recommendations', {})
            suitable_crops = crop_recs.get('suitable_crops', ['Rice (Paddy)', 'Vegetables', 'Sugarcane'])
            farming_advice = crop_recs.get('farming_advice', f'Current conditions are suitable for farming.')
            
            weather_text = f"""
Current weather in {location}: Temperature {temp}°C, Humidity {humidity}%, Soil moisture {moisture}%, Wind Speed {wind_speed} m/s, Rainfall: N/A mm

Based on the current weather conditions in {location}, it is generally favorable for farming this week. Here are some key points to consider:

1. **Temperature**: At {temp}°C, the temperature is suitable for a variety of crops, particularly warm-season crops.

2. **Humidity**: The humidity level is quite high at {humidity}%, which is beneficial for crops that thrive in moist conditions, such as rice (paddy) and certain vegetables.

3. **Soil Moisture**: With soil moisture at {moisture}%, the soil is adequately moist, reducing the need for immediate irrigation. This is particularly advantageous for crops that require consistent moisture levels.

### Recommended Crops: Given the current conditions, the following crops are recommended for planting or maintaining this period:

{chr(10).join([f'• **{crop}**: Suitable for current weather conditions.' for crop in suitable_crops])}

### Farming Advice: 
• **Irrigation**: Since soil moisture is {moisture}%, {'avoid over-irrigating to prevent waterlogging' if float(str(moisture).replace('%', '')) > 60 else 'consider supplemental irrigation if needed'}.
• **Pest Management**: {'High humidity can lead to increased pest activity. Regular monitoring and preventive measures are advisable' if float(str(humidity).replace('%', '')) > 70 else 'Monitor for pests and diseases regularly'}.
• **Fertilization**: Ensure that nutrient levels in the soil are adequate, especially if planting new crops.

{farming_advice}
"""
            return weather_text.strip()
        
        # Get daily forecast data for crop suitability analysis (comprehensive mode)
        daily_forecast = weather_data.get('daily', [])
        
        # Only do expensive crop analysis for comprehensive mode
        if daily_forecast and len(daily_forecast) > 0:
            crop_suitability_analysis = analyze_weather_for_crops(daily_forecast, location)
        else:
            crop_suitability_analysis = f"Limited forecast data available for {location}. Current conditions: {description}."
        
        # Format weather data for RAG processing with crop recommendations
        weather_text = f"""
Weather forecast for {location} covering {timeline_desc} ({data_points} days):
Current: Temperature {temp}°C, Feels like {feels_like}°C, Humidity {humidity}%, 
Description: {description}, Wind speed {wind_speed} m/s, Soil moisture {moisture}%

{crop_suitability_analysis}

This weather data is suitable for agricultural planning, crop selection, and farming decisions.
"""
        
        return weather_text.strip()
        
    except Exception as e:
        return f"Weather data processing error for {location}: {str(e)}"

def refresh_weather_data():
    """Force refresh of weather data in RAG system"""
    try:
        # Remove cached weather data to force refresh
        if os.path.exists(WEATHER_DATA_PATH):
            os.remove(WEATHER_DATA_PATH)
            print("Cached weather data cleared")
        
        # Remove existing index to force rebuild with fresh data
        for file_path in [INDEX_PATH, CHUNKS_CSV, META_PATH, EMBEDDINGS_PATH]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        print("RAG index cleared - will rebuild with fresh weather data on next query")
        return {"status": "success", "message": "Weather data refresh initiated"}
    except Exception as e:
        return {"status": "error", "message": f"Error refreshing weather data: {str(e)}"}

def analyze_weather_for_crops(daily_forecast: List[Dict], location: str) -> str:
    """
    Analyze weather patterns to determine crop suitability
    
    Args:
        daily_forecast: List of daily weather forecasts
        location: Location name
        
    Returns:
        String containing crop suitability analysis
    """
    try:
        if not daily_forecast or len(daily_forecast) == 0:
            return "Insufficient weather data for crop analysis."
        
        # Analyze temperature patterns
        temps = [day.get('temp', 0) for day in daily_forecast if day.get('temp') is not None]
        if temps:
            avg_temp = sum(temps) / len(temps)
            min_temp = min(temps)
            max_temp = max(temps)
            temp_variability = max_temp - min_temp
        else:
            return "Temperature data unavailable for crop analysis."
        
        # Analyze humidity patterns
        humidities = [day.get('humidity', 0) for day in daily_forecast if day.get('humidity') is not None]
        if humidities:
            avg_humidity = sum(humidities) / len(humidities)
        else:
            avg_humidity = 65  # Default humidity
        
        # Analyze precipitation patterns
        precipitations = [day.get('precip_mm', 0) for day in daily_forecast if day.get('precip_mm') is not None]
        if precipitations:
            total_precip = sum(precipitations)
            rainy_days = sum(1 for p in precipitations if p > 0)
        else:
            total_precip = 0
            rainy_days = 0
        
        # Determine crop suitability based on weather patterns
        suitable_crops = []
        crop_reasons = {}
        
        # Temperature-based crop recommendations
        if avg_temp >= 25 and avg_temp <= 35:
            crops = ["Rice", "Maize", "Cotton", "Sugarcane", "Groundnut", "Pulses"]
            suitable_crops.extend(crops)
            for crop in crops:
                crop_reasons[crop] = f"Optimal temperature range ({avg_temp:.1f}°C) for {crop.lower()} growth"
        elif avg_temp >= 20 and avg_temp <= 30:
            crops = ["Wheat", "Barley", "Peas", "Lentils", "Mustard", "Chickpea"]
            suitable_crops.extend(crops)
            for crop in crops:
                crop_reasons[crop] = f"Moderate temperature ({avg_temp:.1f}°C) suitable for {crop.lower()}"
        elif avg_temp >= 15 and avg_temp <= 25:
            crops = ["Potato", "Carrot", "Cabbage", "Cauliflower", "Spinach", "Onion"]
            suitable_crops.extend(crops)
            for crop in crops:
                crop_reasons[crop] = f"Cool temperature ({avg_temp:.1f}°C) ideal for {crop.lower()}"
        
        # Humidity-based adjustments
        if avg_humidity >= 70:
            crops = ["Rice", "Tea", "Coffee", "Spices", "Jute"]
            suitable_crops.extend(crops)
            for crop in crops:
                if crop not in crop_reasons:
                    crop_reasons[crop] = f"High humidity ({avg_humidity:.1f}%) beneficial for {crop.lower()}"
        elif avg_humidity <= 40:
            crops = ["Millet", "Sorghum", "Sunflower", "Sesame", "Groundnut"]
            suitable_crops.extend(crops)
            for crop in crops:
                if crop not in crop_reasons:
                    crop_reasons[crop] = f"Low humidity ({avg_humidity:.1f}%) suitable for {crop.lower()}"
        
        # Precipitation-based recommendations
        if total_precip >= 100:  # High rainfall
            crops = ["Rice", "Jute", "Tea", "Rubber", "Sugarcane"]
            suitable_crops.extend(crops)
            for crop in crops:
                if crop not in crop_reasons:
                    crop_reasons[crop] = f"High rainfall ({total_precip:.1f}mm) supports {crop.lower()} cultivation"
        elif total_precip <= 30:  # Low rainfall
            crops = ["Millet", "Sorghum", "Sunflower", "Sesame", "Groundnut"]
            suitable_crops.extend(crops)
            for crop in crops:
                if crop not in crop_reasons:
                    crop_reasons[crop] = f"Low rainfall ({total_precip:.1f}mm) suitable for drought-resistant {crop.lower()}"
        
        # Remove duplicates and limit to top recommendations
        suitable_crops = list(set(suitable_crops))[:10]
        
        # Sort crops by suitability score
        crop_scores = {}
        for crop in suitable_crops:
            score = 0
            if crop in crop_reasons:
                if "optimal" in crop_reasons[crop].lower():
                    score += 3
                elif "suitable" in crop_reasons[crop].lower():
                    score += 2
                else:
                    score += 1
            crop_scores[crop] = score
        
        # Sort by score (highest first)
        suitable_crops = sorted(suitable_crops, key=lambda x: crop_scores.get(x, 0), reverse=True)
        
        # Generate analysis text
        analysis = f"""
Crop Suitability Analysis for {location}:
• Average Temperature: {avg_temp:.1f}°C (Range: {min_temp:.1f}°C to {max_temp:.1f}°C)
• Temperature Variability: {temp_variability:.1f}°C
• Average Humidity: {avg_humidity:.1f}%
• Total Precipitation: {total_precip:.1f}mm over {len(daily_forecast)} days
• Rainy Days: {rainy_days} out of {len(daily_forecast)} days

Top Recommended Crops:
"""
        
        # Add top 5 crops with reasons
        for i, crop in enumerate(suitable_crops[:5], 1):
            reason = crop_reasons.get(crop, "Suitable for current weather conditions")
            analysis += f"{i}. {crop}: {reason}\n"
        
        analysis += f"""
Additional Suitable Crops: {', '.join(suitable_crops[5:])}

Weather Conditions: {'Stable' if temp_variability < 10 else 'Variable'} temperature with {'High' if avg_humidity >= 70 else 'Moderate' if avg_humidity >= 50 else 'Low'} humidity.
"""
        
        return analysis.strip()
        
    except Exception as e:
        return f"Crop analysis error: {str(e)}"

def add_weather_data_to_existing_index(weather_data: Dict[str, Any], location: str) -> bool:
    """
    Add weather data to existing RAG index without rebuilding
    
    Args:
        weather_data: Weather data from weather service
        location: Location name
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(INDEX_PATH) or not os.path.exists(CHUNKS_CSV):
            print("No existing index found, cannot add weather data")
            return False
        
        # Load existing chunks
        df_chunks = pd.read_csv(CHUNKS_CSV)
        
        # Check if weather data for this location already exists
        weather_files = [f for f in df_chunks['source_file'] if f.startswith(f'weather_data_{location}')]
        if weather_files:
            print(f"Weather data for {location} already exists in index")
            return True
        
        # Add new weather data
        weather_text = feed_weather_data_to_rag(weather_data, location)
        if weather_text and "error" not in weather_text.lower():
            weather_chunk = {
                'text': weather_text,
                'source_file': f'weather_data_{location}_{time.strftime("%Y%m%d")}.txt',
                'chunk_id': f'weather_{location}_{int(time.time())}'
            }
            
            # Add to existing chunks
            df_chunks = pd.concat([df_chunks, pd.DataFrame([weather_chunk])], ignore_index=True)
            
            # Save updated chunks
            df_chunks.to_csv(CHUNKS_CSV, index=False)
            
            # Rebuild index with new data
            model_name = config.EMBEDDING_MODEL
            embedder = SentenceTransformer(model_name, device="cpu")
            texts = df_chunks["text"].tolist()
            new_index = build_faiss_index_safe(texts, embedder)
            
            # Save new index
            faiss.write_index(new_index, INDEX_PATH)
            
            # Update metadata
            meta = {
                "model_name": model_name, 
                "total_chunks": len(df_chunks), 
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "weather_locations": list(set([f.split('_')[2] for f in df_chunks['source_file'] if f.startswith('weather_data_')]))
            }
            
            with open(META_PATH, 'w') as f:
                json.dump(meta, f, indent=2)
            
            print(f"✅ Successfully added weather data for {location} to existing RAG index")
            return True
            
    except Exception as e:
        print(f"❌ Error adding weather data to existing index: {e}")
        return False

def get_rag_status():
    """Get status of RAG system"""
    try:
        index_exists = os.path.exists(INDEX_PATH)
        cache_exists = os.path.exists(WEATHER_DATA_PATH)
        cache_age = None
        
        if cache_exists:
            cache_age = int((time.time() - os.path.getmtime(WEATHER_DATA_PATH)) / 60)  # Age in minutes
        
        chunk_count = 0
        weather_locations = []
        if os.path.exists(CHUNKS_CSV):
            try:
                df = pd.read_csv(CHUNKS_CSV)
                chunk_count = len(df)
                # Extract weather locations from source files
                weather_files = [f for f in df['source_file'] if f.startswith('weather_data_')]
                weather_locations = list(set([f.split('_')[2] for f in weather_files]))
            except:
                pass
        
        return {
            "status": "ready" if index_exists else "needs_initialization",
            "index_exists": index_exists,
            "weather_cache_exists": cache_exists,
            "weather_cache_age_minutes": cache_age,
            "total_chunks": chunk_count,
            "weather_locations": weather_locations,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ==== Main function ====
def main():
    print(" Starting memory-optimized agriculture assistant...")
    start_time = time.time()
    try:
        print("Loading embedding model...")
        model_name = config.EMBEDDING_MODEL
        embedder = SentenceTransformer(model_name, device="cpu")
        index, df_chunks, meta = load_index()
        if index is None:
            df_chunks = load_all_data()
            print(f"Processing {len(df_chunks)} text chunks")
            texts = df_chunks["text"].tolist()
            index = build_faiss_index_safe(texts, embedder)
            meta = {"model_name": model_name, "total_chunks": len(df_chunks), "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            save_index(index, df_chunks, meta)
        print(f"Ready with {len(df_chunks)} chunks")

        def preprocess_query(q: str) -> str: 
            q = q.lower().replace("rice", "paddy") 
            return q


        while True:
            query = input("\n🔍 Enter your query (or 'quit' to exit): ").strip()
            query = preprocess_query(query)
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if not query:
                continue
            indices, scores = faiss_search(query, embedder, index)
            if len(indices) == 0:
                print("No relevant results found.")
                continue
            valid_indices = indices[indices < len(df_chunks)]
            if len(valid_indices) == 0:
                print("No valid results found.")
                continue
            retrieved = df_chunks.iloc[valid_indices[:5]]
            context_parts = []
            for i, (_, row) in enumerate(retrieved.iterrows()):
                if i < len(scores) and scores[i] > 0.2:
                    context_parts.append(f"- {row['text']} (source: {row['source_file']})")
            if not context_parts:
                print(" No sufficiently relevant results found.")
                continue
            context = "\n".join(context_parts)

            template = ChatPromptTemplate.from_template(f"""
You are an Agriculture assistant.
- Use the context tables to interpolate/extrapolate values when queries involve numeric estimates (e.g., cost of cultivation → yield).
- Always show your calculation steps.
- If no relevant numeric context is found, reply "Data not available".
- Treat "rice" as equivalent to "paddy".
-If the query includes a numeric value that does not exactly match the dataset, 
analyze the nearest available values and explain the estimated trend 
(e.g., "for cultivation cost slightly lower/higher than X, the yield increases/decreases, 
so the expected value is around Y").
-- If no relevant numeric context is found, DO NOT reply "Data not available".
  Instead, fall back to general agricultural knowledge (e.g., cotton usually takes 150–180 days to harvest).
                                                        


{few_shots}

Context:
{{context}}

Query:
{{query}}
""")

            try:
                final_prompt = template.format(context=context, query=query)
                llm = ChatOpenAI(model=config.OPENAI_MODEL, temperature=config.LLM_TEMPERATURE_ZERO)
                response = llm.invoke(final_prompt)
                print("\n ANSWER:")
                print("-" * 50)
                print(response.content.strip())
                print("-" * 50)
            except Exception as e:
                print(f" Error generating response: {e}")
    except KeyboardInterrupt:
        print("\n Goodbye!")
    except Exception as e:
        print(f" Fatal error: {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()
