"""
Timeline Extractor for Weather Queries
Extracts time periods from user queries to determine weather data retrieval duration
"""

import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

class TimelineExtractor:
    """Extracts timeline information from user queries"""
    
    def __init__(self):
        # Common time period patterns
        self.time_patterns = {
            # Days
            r'\b(\d+)\s*days?\b': 'days',
            r'\b(\d+)\s*d\b': 'days',
            
            # Weeks
            r'\b(\d+)\s*weeks?\b': 'weeks',
            r'\b(\d+)\s*w\b': 'weeks',
            r'\bone\s+week\b': 'weeks',
            r'\btwo\s+weeks\b': 'weeks',
            r'\bthree\s+weeks\b': 'weeks',
            r'\bfour\s+weeks\b': 'weeks',
            r'\bthis\s+week\b': 'weeks',
            r'\bnext\s+week\b': 'weeks',
            r'\bcurrent\s+week\b': 'weeks',
            
            # Months
            r'\b(\d+)\s*months?\b': 'months',
            r'\b(\d+)\s*mo\b': 'months',
            r'\bone\s+month\b': 'months',
            r'\btwo\s+months\b': 'months',
            r'\bthree\s+months\b': 'months',
            r'\bfour\s+months\b': 'months',
            r'\bthis\s+month\b': 'months',
            r'\bnext\s+month\b': 'months',
            
            # Specific time periods
            r'\bnext\s+(\d+)\s*days?\b': 'days',
            r'\bnext\s+(\d+)\s*weeks?\b': 'weeks',
            r'\bnext\s+(\d+)\s*months?\b': 'months',
            r'\bupcoming\s+(\d+)\s*days?\b': 'days',
            r'\bupcoming\s+(\d+)\s*weeks?\b': 'weeks',
            r'\bupcoming\s+(\d+)\s*months?\b': 'months',
            
            # Seasonal references
            r'\bthis\s+season\b': 'season',
            r'\bcurrent\s+season\b': 'season',
            r'\bnext\s+season\b': 'season',
            
            # Agricultural context patterns
            r'\bcrop\s+season\b': 'season',
            r'\bplanting\s+season\b': 'season',
            r'\bharvest\s+season\b': 'season',
            r'\bgrowing\s+season\b': 'season',
        }
        
        # Default periods for different query types
        self.default_periods = {
            'weather_forecast': 7,  # 7 days for general weather queries
            'agricultural_planning': 120,  # 120 days for crop planning
            'crop_suitability': 120,  # 120 days for crop suitability analysis
            'seed_variety': 120,  # 120 days for seed variety recommendations
            'general_question': 120,  # 120 days for general agricultural questions
        }
    
    def extract_timeline(self, query: str) -> Dict[str, Any]:
        """
        Extract timeline information from a query
        
        Args:
            query (str): User query text
            
        Returns:
            Dict containing timeline information
        """
        query_lower = query.lower().strip()
        
        # Check for specific time periods first
        for pattern, unit in self.time_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                if unit == 'days':
                    days = int(match.group(1))
                    return {
                        'type': 'specific_period',
                        'unit': 'days',
                        'value': days,
                        'total_days': days,
                        'description': f'{days} days'
                    }
                elif unit == 'weeks':
                    if 'one week' in query_lower or 'this week' in query_lower or 'next week' in query_lower or 'current week' in query_lower:
                        days = 7
                    elif 'two weeks' in query_lower:
                        days = 14
                    elif 'three weeks' in query_lower:
                        days = 21
                    elif 'four weeks' in query_lower:
                        days = 28
                    else:
                        weeks = int(match.group(1))
                        days = weeks * 7
                    return {
                        'type': 'specific_period',
                        'unit': 'weeks',
                        'value': days // 7,
                        'total_days': days,
                        'description': f'{days // 7} weeks ({days} days)'
                    }
                elif unit == 'months':
                    if 'one month' in query_lower or 'this month' in query_lower or 'next month' in query_lower:
                        days = 30
                    elif 'two months' in query_lower:
                        days = 60
                    elif 'three months' in query_lower:
                        days = 90
                    elif 'four months' in query_lower:
                        days = 120
                    else:
                        months = int(match.group(1))
                        days = months * 30
                    return {
                        'type': 'specific_period',
                        'unit': 'months',
                        'value': days // 30,
                        'total_days': days,
                        'description': f'{days // 30} months ({days} days)'
                    }
                elif unit == 'season':
                    return {
                        'type': 'seasonal',
                        'unit': 'season',
                        'value': 1,
                        'total_days': 120,  # 4 months for a season
                        'description': 'seasonal period (120 days)'
                    }
        
        # Check for agricultural context patterns (only if no specific timeline was found)
        if self._is_agricultural_query(query_lower):
            return {
                'type': 'agricultural_default',
                'unit': 'days',
                'value': 120,
                'total_days': 120,
                'description': 'agricultural planning period (120 days)'
            }
        
        # Default to 7 days for general weather queries
        return {
            'type': 'default',
            'unit': 'days',
            'value': 7,
            'total_days': 7,
            'description': 'default period (7 days)'
        }
    
    def _is_agricultural_query(self, query: str) -> bool:
        """
        Check if query is agricultural in nature
        
        Args:
            query (str): Lowercase query text
            
        Returns:
            bool: True if agricultural query
        """
        agricultural_keywords = [
            'crop', 'seed', 'plant', 'harvest', 'grow', 'agriculture',
            'suitable', 'variety', 'soil', 'moisture', 'temperature',
            'planting', 'growing', 'season', 'unpredictable', 'climate',
            'agricultural', 'cultivation', 'yield', 'production'
        ]
        
        # Don't mark as agricultural if it's just asking about weather
        # (which is more of a weather query than agricultural planning)
        if any(word in query for word in ['weather', 'forecast', 'conditions']) and not any(word in query for word in ['crop', 'seed', 'plant', 'harvest', 'grow', 'agriculture', 'farming', 'farm']):
            return False
        
        # Don't mark as agricultural if it's just asking about weather for farming
        # (which is more of a weather query than agricultural planning)
        if any(word in query for word in ['farming', 'farm']) and not any(word in query for word in ['crop', 'seed', 'plant', 'harvest', 'grow', 'agriculture']):
            return False
        
        return any(keyword in query for keyword in agricultural_keywords)
    
    def get_weather_data_period(self, query: str) -> int:
        """
        Get the number of days to retrieve weather data for
        
        Args:
            query (str): User query
            
        Returns:
            int: Number of days (1-120)
        """
        timeline = self.extract_timeline(query)
        return min(timeline['total_days'], 120)  # Cap at 120 days
    
    def get_timeline_description(self, query: str) -> str:
        """
        Get a human-readable description of the timeline
        
        Args:
            query (str): User query
            
        Returns:
            str: Timeline description
        """
        timeline = self.extract_timeline(query)
        return timeline['description']
