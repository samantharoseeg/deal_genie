#!/usr/bin/env python3
"""
TOC Tier Engine
===============

Core TOC tier calculation engine with improved architecture.
Separated concerns for better maintainability and testing.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from toc_config import TOCConfig
from toc_distance_calculator import TOCDistanceCalculator, TOCDistanceCalculatorError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TOCResult:
    """Data class for TOC calculation results"""
    toc_tier: int
    bonus_points: int
    description: str
    nearest_station: str
    distance_feet: float
    station_type: str
    station_line: str
    calculation_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for compatibility"""
        return {
            'toc_tier': self.toc_tier,
            'bonus_points': self.bonus_points,
            'description': self.description,
            'nearest_station': self.nearest_station,
            'distance_feet': self.distance_feet,
            'station_type': self.station_type,
            'station_line': self.station_line
        }


class TOCTierEngineError(Exception):
    """Custom exception for TOC tier engine errors"""
    pass


class TOCTierEngine:
    """
    Refactored TOC tier calculation engine
    
    Improved architecture with separated concerns:
    - Configuration management externalized
    - Distance calculations optimized and cached
    - Error handling standardized
    - Performance monitoring built-in
    """
    
    def __init__(self, config: Optional[TOCConfig] = None, enable_caching: bool = True):
        """
        Initialize TOC tier engine
        
        Args:
            config: TOC configuration object (creates default if None)
            enable_caching: Enable distance calculation caching
        """
        self.config = config or TOCConfig()
        self.distance_calculator = TOCDistanceCalculator(enable_caching=enable_caching)
        
        # Preprocess station data for performance
        self.rail_stations = self._prepare_stations('rail_stations')
        self.rapid_bus_stations = self._prepare_stations('rapid_bus_stations')
        self.bus_intersections = self._prepare_stations('bus_intersections')
        
        # Performance tracking
        self.calculations_performed = 0
        self.total_processing_time = 0.0
        
        logger.info(f"TOC Tier Engine initialized with {self._get_total_station_count()} stations")
    
    def _prepare_stations(self, station_type: str) -> List[Dict]:
        """Prepare station data with validation"""
        stations = self.config.station_config.get(station_type, [])
        validated_stations = []
        
        for station in stations:
            if self._validate_station_data(station):
                validated_stations.append(station)
            else:
                logger.warning(f"Invalid station data: {station}")
        
        return validated_stations
    
    def _validate_station_data(self, station: Dict) -> bool:
        """Validate station data completeness"""
        required_fields = ['name', 'lat', 'lon', 'type']
        
        for field in required_fields:
            if field not in station or station[field] is None:
                return False
        
        # Validate coordinates
        return self.distance_calculator.validate_coordinates(
            station['lat'], station['lon']
        )
    
    def _get_total_station_count(self) -> int:
        """Get total number of valid stations"""
        return (len(self.rail_stations) + 
                len(self.rapid_bus_stations) + 
                len(self.bus_intersections))
    
    def calculate_toc_tier(self, property_lat: float, property_lon: float) -> TOCResult:
        """
        Calculate TOC tier for property coordinates
        
        Args:
            property_lat: Property latitude
            property_lon: Property longitude
            
        Returns:
            TOCResult object with tier calculation results
            
        Raises:
            TOCTierEngineError: If calculation fails
        """
        import time
        start_time = time.time()
        
        try:
            # Validate input coordinates
            if not self.distance_calculator.validate_coordinates(property_lat, property_lon):
                return self._create_invalid_result("Invalid coordinates provided")
            
            # Find nearest stations by type
            nearest_stations = self._find_nearest_stations_by_type(property_lat, property_lon)
            
            # Calculate TOC tier based on distances and rules
            tier_result = self._determine_toc_tier(nearest_stations)
            
            # Update performance counters
            calculation_time = (time.time() - start_time) * 1000
            self.calculations_performed += 1
            self.total_processing_time += calculation_time
            
            tier_result.calculation_time_ms = calculation_time
            
            return tier_result
            
        except Exception as e:
            logger.error(f"TOC tier calculation failed for ({property_lat}, {property_lon}): {str(e)}")
            raise TOCTierEngineError(f"TOC calculation failed: {str(e)}") from e
    
    def _find_nearest_stations_by_type(self, property_lat: float, property_lon: float) -> Dict:
        """Find nearest station of each type"""
        nearest_stations = {}
        
        station_types = [
            ('rail', self.rail_stations),
            ('rapid_bus', self.rapid_bus_stations),
            ('bus_intersection', self.bus_intersections)
        ]
        
        for station_type, stations in station_types:
            try:
                if stations:  # Only search if stations exist
                    nearest = self.distance_calculator.find_nearest_station(
                        property_lat, property_lon, stations
                    )
                    nearest_stations[station_type] = nearest
                else:
                    nearest_stations[station_type] = {
                        'distance': float('inf'),
                        'station': None,
                        'station_info': None
                    }
            except TOCDistanceCalculatorError as e:
                logger.warning(f"Failed to find nearest {station_type}: {str(e)}")
                nearest_stations[station_type] = {
                    'distance': float('inf'),
                    'station': None,
                    'station_info': None
                }
        
        return nearest_stations
    
    def _determine_toc_tier(self, nearest_stations: Dict) -> TOCResult:
        """
        Determine TOC tier based on distance rules
        
        Implements LA City Planning TOC guidelines:
        - Tier 4: ≤750ft from rail/rapid bus
        - Tier 3: 751-1500ft from rail OR ≤750ft from bus intersection
        - Tier 2: 1501-2640ft from rail/rapid bus
        - Tier 1: 751-2640ft from bus intersection
        - Tier 0: >2640ft from any transit
        """
        rail_dist = nearest_stations['rail']['distance']
        rapid_bus_dist = nearest_stations['rapid_bus']['distance']
        bus_intersection_dist = nearest_stations['bus_intersection']['distance']
        
        # Tier 4: Within 750 feet of rail/rapid bus
        if rail_dist <= 750 or rapid_bus_dist <= 750:
            best_station = (nearest_stations['rail'] if rail_dist <= rapid_bus_dist 
                          else nearest_stations['rapid_bus'])
            return self._create_tier_result(4, best_station)
        
        # Tier 3: 751-1500 feet from rail OR within 750 feet of bus intersection
        if rail_dist <= 1500:
            return self._create_tier_result(3, nearest_stations['rail'])
        
        if bus_intersection_dist <= 750:
            return self._create_tier_result(3, nearest_stations['bus_intersection'])
        
        # Tier 2: 1501-2640 feet from rail/rapid bus
        if rail_dist <= 2640 or rapid_bus_dist <= 2640:
            best_station = (nearest_stations['rail'] if rail_dist <= rapid_bus_dist 
                          else nearest_stations['rapid_bus'])
            return self._create_tier_result(2, best_station)
        
        # Tier 1: 751-2640 feet from bus intersection
        if bus_intersection_dist <= 2640:
            return self._create_tier_result(1, nearest_stations['bus_intersection'])
        
        # Tier 0: Beyond 2640 feet from any transit
        # Show nearest station for reference
        all_stations = [
            ('rail', nearest_stations['rail']),
            ('rapid_bus', nearest_stations['rapid_bus']),
            ('bus_intersection', nearest_stations['bus_intersection'])
        ]
        
        valid_stations = [(name, station) for name, station in all_stations 
                         if station['distance'] != float('inf')]
        
        if valid_stations:
            _, best_station = min(valid_stations, key=lambda x: x[1]['distance'])
            return self._create_tier_result(0, best_station)
        else:
            return self._create_invalid_result("No valid stations found")
    
    def _create_tier_result(self, tier: int, station_info: Dict) -> TOCResult:
        """Create TOCResult object for valid tier"""
        tier_config = self.config.get_tier_config(tier)
        station_data = station_info.get('station_info', {})
        
        return TOCResult(
            toc_tier=tier,
            bonus_points=tier_config['bonus_points'],
            description=tier_config['description'],
            nearest_station=station_info.get('station', 'Unknown'),
            distance_feet=round(station_info.get('distance', 0), 0),
            station_type=station_data.get('type', 'unknown'),
            station_line=station_data.get('line', 'Unknown')
        )
    
    def _create_invalid_result(self, reason: str) -> TOCResult:
        """Create TOCResult for invalid/error cases"""
        return TOCResult(
            toc_tier=0,
            bonus_points=0,
            description=f"No TOC Tier - {reason}",
            nearest_station="None",
            distance_feet=0.0,
            station_type="none",
            station_line="None"
        )
    
    def process_properties_batch(self, properties_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process multiple properties efficiently
        
        Args:
            properties_df: DataFrame with property coordinates
            
        Returns:
            DataFrame with TOC tier results added
        """
        logger.info(f"Processing TOC tiers for {len(properties_df)} properties")
        
        # Identify coordinate columns
        lat_col = self._find_coordinate_column(properties_df, ['latitude', 'lat', 'property_lat'])
        lon_col = self._find_coordinate_column(properties_df, ['longitude', 'lon', 'lng', 'property_lon'])
        
        if not lat_col or not lon_col:
            raise TOCTierEngineError("Could not find latitude/longitude columns in DataFrame")
        
        toc_results = []
        batch_size = 100
        
        for idx in range(0, len(properties_df), batch_size):
            batch_end = min(idx + batch_size, len(properties_df))
            batch = properties_df.iloc[idx:batch_end]
            
            logger.info(f"Processing batch {idx//batch_size + 1}: properties {idx+1}-{batch_end}")
            
            for _, row in batch.iterrows():
                lat = row[lat_col]
                lon = row[lon_col]
                
                try:
                    result = self.calculate_toc_tier(lat, lon)
                    toc_results.append(result.to_dict())
                except TOCTierEngineError:
                    # Add invalid result for failed calculations
                    invalid_result = self._create_invalid_result("Calculation failed")
                    toc_results.append(invalid_result.to_dict())
        
        # Add results to DataFrame
        toc_df = pd.DataFrame(toc_results)
        for col in toc_df.columns:
            properties_df[f'toc_{col}'] = toc_df[col]
        
        # Generate summary statistics
        self._log_processing_summary(properties_df)
        
        return properties_df
    
    def _find_coordinate_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find coordinate column from possible names"""
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    def _log_processing_summary(self, properties_df: pd.DataFrame) -> None:
        """Log processing summary statistics"""
        tier_distribution = properties_df['toc_toc_tier'].value_counts().sort_index()
        
        logger.info("TOC Tier Distribution:")
        for tier, count in tier_distribution.items():
            tier_config = self.config.get_tier_config(tier)
            percentage = (count / len(properties_df)) * 100
            logger.info(f"  Tier {tier} (+{tier_config['bonus_points']} points): "
                       f"{count} properties ({percentage:.1f}%)")
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for monitoring"""
        distance_stats = self.distance_calculator.get_performance_stats()
        
        avg_calc_time = (self.total_processing_time / max(self.calculations_performed, 1))
        
        return {
            'calculations_performed': self.calculations_performed,
            'average_calculation_time_ms': round(avg_calc_time, 2),
            'total_processing_time_ms': round(self.total_processing_time, 2),
            'distance_calculator_stats': distance_stats,
            'total_stations': self._get_total_station_count()
        }
    
    def validate_engine_health(self) -> Dict:
        """Validate engine health and configuration"""
        health_check = {
            'status': 'healthy',
            'issues': [],
            'station_counts': {
                'rail_stations': len(self.rail_stations),
                'rapid_bus_stations': len(self.rapid_bus_stations),
                'bus_intersections': len(self.bus_intersections)
            }
        }
        
        # Check for missing stations
        if not self.rail_stations:
            health_check['issues'].append("No rail stations configured")
        
        if not self.bus_intersections:
            health_check['issues'].append("No bus intersections configured")
        
        # Check distance calculator
        try:
            test_distance = self.distance_calculator.calculate_distance_feet(
                34.0522, -118.2437, 34.0523, -118.2438
            )
            if test_distance <= 0:
                health_check['issues'].append("Distance calculator returning invalid results")
        except Exception as e:
            health_check['issues'].append(f"Distance calculator error: {str(e)}")
        
        if health_check['issues']:
            health_check['status'] = 'degraded'
        
        return health_check