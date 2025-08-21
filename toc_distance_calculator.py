#!/usr/bin/env python3
"""
TOC Distance Calculator
======================

High-performance distance calculation module for TOC tier system.
Optimized for batch processing and caching.
"""

import math
import pandas as pd
from typing import Dict, List, Tuple, Optional
from functools import lru_cache
import numpy as np


class TOCDistanceCalculatorError(Exception):
    """Custom exception for TOC distance calculation errors"""
    pass


class TOCDistanceCalculator:
    """Optimized distance calculator for TOC tier calculations"""
    
    def __init__(self, enable_caching: bool = True):
        """
        Initialize distance calculator
        
        Args:
            enable_caching: Enable LRU caching for repeated calculations
        """
        self.enable_caching = enable_caching
        self.earth_radius_feet = 20902231  # Earth radius in feet
        
        # Performance counters
        self.calculation_count = 0
        self.cache_hits = 0
    
    def calculate_distance_feet(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two lat/lon points in feet using Haversine formula
        
        Args:
            lat1, lon1: First coordinate pair
            lat2, lon2: Second coordinate pair
            
        Returns:
            Distance in feet
            
        Raises:
            TOCDistanceCalculatorError: If coordinates are invalid
        """
        # Input validation
        if any(pd.isna([lat1, lon1, lat2, lon2])):
            raise TOCDistanceCalculatorError("Cannot calculate distance with NaN coordinates")
        
        if not all(-90 <= lat <= 90 for lat in [lat1, lat2]):
            raise TOCDistanceCalculatorError(f"Invalid latitude values: {lat1}, {lat2}")
        
        if not all(-180 <= lon <= 180 for lon in [lon1, lon2]):
            raise TOCDistanceCalculatorError(f"Invalid longitude values: {lon1}, {lon2}")
        
        self.calculation_count += 1
        
        try:
            if self.enable_caching:
                return self._cached_distance_calculation(lat1, lon1, lat2, lon2)
            else:
                return self._haversine_distance(lat1, lon1, lat2, lon2)
                
        except Exception as e:
            raise TOCDistanceCalculatorError(f"Distance calculation failed: {str(e)}") from e
    
    @lru_cache(maxsize=10000)
    def _cached_distance_calculation(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Cached version of distance calculation"""
        self.cache_hits += 1
        return self._haversine_distance(lat1, lon1, lat2, lon2)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Core Haversine formula implementation
        
        Optimized for accuracy and performance
        """
        # Convert to radians
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        return c * self.earth_radius_feet
    
    def calculate_distances_batch(self, 
                                 property_coords: List[Tuple[float, float]], 
                                 station_coords: List[Tuple[float, float]]) -> np.ndarray:
        """
        Calculate distances between multiple properties and stations efficiently
        
        Args:
            property_coords: List of (lat, lon) tuples for properties
            station_coords: List of (lat, lon) tuples for stations
            
        Returns:
            2D numpy array where [i,j] is distance from property i to station j
        """
        if not property_coords or not station_coords:
            raise TOCDistanceCalculatorError("Cannot calculate batch distances with empty coordinate lists")
        
        # Vectorized distance calculation for better performance
        distances = np.zeros((len(property_coords), len(station_coords)))
        
        for i, (prop_lat, prop_lon) in enumerate(property_coords):
            for j, (station_lat, station_lon) in enumerate(station_coords):
                try:
                    distances[i, j] = self.calculate_distance_feet(
                        prop_lat, prop_lon, station_lat, station_lon
                    )
                except TOCDistanceCalculatorError:
                    distances[i, j] = float('inf')
        
        return distances
    
    def find_nearest_station(self, 
                           property_lat: float, 
                           property_lon: float, 
                           stations: List[Dict]) -> Dict:
        """
        Find nearest station to a property with optimized search
        
        Args:
            property_lat, property_lon: Property coordinates
            stations: List of station dictionaries with lat/lon
            
        Returns:
            Dictionary with nearest station info and distance
        """
        if not stations:
            raise TOCDistanceCalculatorError("No stations provided for nearest station search")
        
        nearest = {
            'station': None,
            'distance': float('inf'),
            'station_info': None
        }
        
        for station in stations:
            try:
                station_lat = station.get('lat')
                station_lon = station.get('lon')
                
                if station_lat is None or station_lon is None:
                    continue
                
                distance = self.calculate_distance_feet(
                    property_lat, property_lon, station_lat, station_lon
                )
                
                if distance < nearest['distance']:
                    nearest.update({
                        'station': station.get('name', 'Unknown'),
                        'distance': distance,
                        'station_info': station
                    })
                    
            except TOCDistanceCalculatorError:
                continue  # Skip invalid stations
        
        if nearest['station'] is None:
            raise TOCDistanceCalculatorError("No valid stations found for distance calculation")
        
        return nearest
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics for monitoring"""
        cache_hit_rate = (self.cache_hits / max(self.calculation_count, 1)) * 100
        
        return {
            'total_calculations': self.calculation_count,
            'cache_hits': self.cache_hits,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'cache_enabled': self.enable_caching
        }
    
    def clear_cache(self) -> None:
        """Clear distance calculation cache"""
        if hasattr(self, '_cached_distance_calculation'):
            self._cached_distance_calculation.cache_clear()
        self.cache_hits = 0
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Validate coordinate values
        
        Args:
            lat: Latitude value
            lon: Longitude value
            
        Returns:
            True if coordinates are valid
        """
        try:
            if pd.isna(lat) or pd.isna(lon):
                return False
            
            if not (-90 <= lat <= 90):
                return False
            
            if not (-180 <= lon <= 180):
                return False
            
            return True
            
        except (TypeError, ValueError):
            return False


class DistanceCache:
    """Persistent cache for distance calculations"""
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize distance cache with optional file persistence"""
        self.cache_file = cache_file
        self.cache = {}
        
        if cache_file:
            self.load_cache()
    
    def get_cache_key(self, lat1: float, lon1: float, lat2: float, lon2: float) -> str:
        """Generate cache key for coordinate pair"""
        # Round to 6 decimal places for cache key consistency
        return f"{lat1:.6f},{lon1:.6f}|{lat2:.6f},{lon2:.6f}"
    
    def get_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        """Get cached distance if available"""
        key = self.get_cache_key(lat1, lon1, lat2, lon2)
        # Also check reverse direction
        reverse_key = self.get_cache_key(lat2, lon2, lat1, lon1)
        
        return self.cache.get(key) or self.cache.get(reverse_key)
    
    def set_distance(self, lat1: float, lon1: float, lat2: float, lon2: float, distance: float) -> None:
        """Cache calculated distance"""
        key = self.get_cache_key(lat1, lon1, lat2, lon2)
        self.cache[key] = distance
    
    def save_cache(self) -> None:
        """Save cache to file if configured"""
        if self.cache_file:
            import json
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
    
    def load_cache(self) -> None:
        """Load cache from file if available"""
        if self.cache_file:
            try:
                import json
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except FileNotFoundError:
                self.cache = {}
            except json.JSONDecodeError:
                self.cache = {}
    
    def clear_cache(self) -> None:
        """Clear all cached distances"""
        self.cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of cached entries"""
        return len(self.cache)