#!/usr/bin/env python3
"""
TOC Configuration Management
============================

Centralized configuration for Transit-Oriented Communities (TOC) system.
Externalized from calculator for better maintainability and testing.
"""

from typing import Dict, List, Tuple
import json
from pathlib import Path


class TOCConfig:
    """Configuration manager for TOC tier system"""
    
    def __init__(self):
        """Initialize TOC configuration"""
        self.tier_thresholds = self._load_tier_definitions()
        self.station_config = self._load_station_config()
    
    def _load_tier_definitions(self) -> Dict:
        """Load TOC tier threshold definitions"""
        return {
            4: {
                'max_distance': 750,
                'bonus_points': 15,
                'description': 'Tier 4 - Rail/Rapid Bus Adjacent',
                'eligibility': ['rail', 'rapid_bus']
            },
            3: {
                'max_distance': 1500,
                'bonus_points': 12,
                'description': 'Tier 3 - Rail Proximity/Bus Intersection',
                'eligibility': ['rail', 'bus_intersection']
            },
            2: {
                'max_distance': 2640,
                'bonus_points': 8,
                'description': 'Tier 2 - Transit Zone',
                'eligibility': ['rail', 'rapid_bus']
            },
            1: {
                'max_distance': 2640,
                'bonus_points': 5,
                'description': 'Tier 1 - Transit Edge',
                'eligibility': ['bus_intersection']
            },
            0: {
                'max_distance': float('inf'),
                'bonus_points': 0,
                'description': 'No TOC Tier',
                'eligibility': []
            }
        }
    
    def _load_station_config(self) -> Dict:
        """Load station configuration"""
        return {
            'rail_stations': self._get_rail_stations(),
            'bus_intersections': self._get_bus_intersections(),
            'rapid_bus_stations': self._get_rapid_bus_stations()
        }
    
    def _get_rail_stations(self) -> List[Dict]:
        """Get LA Metro rail station definitions"""
        return [
            # RED LINE (B Line)
            {'name': 'Union Station', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.056207, 'lon': -118.234468},
            {'name': 'Civic Center/Grand Park', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.056220, 'lon': -118.249481},
            {'name': 'Pershing Square', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.048653, 'lon': -118.251930},
            {'name': 'MacArthur Park', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.057370, 'lon': -118.275734},
            {'name': 'Westlake/MacArthur Park', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.058205, 'lon': -118.277092},
            {'name': 'Hollywood/Western', 'line': 'Red', 'type': 'rail', 'lat': 34.101707, 'lon': -118.309471},
            {'name': 'Hollywood/Vine', 'line': 'Red', 'type': 'rail', 'lat': 34.102252, 'lon': -118.326499},
            {'name': 'Hollywood/Highland', 'line': 'Red', 'type': 'rail', 'lat': 34.102403, 'lon': -118.338974},
            {'name': 'Universal City', 'line': 'Red', 'type': 'rail', 'lat': 34.138855, 'lon': -118.353230},
            {'name': 'North Hollywood', 'line': 'Red', 'type': 'rail', 'lat': 34.168710, 'lon': -118.376668},
            
            # PURPLE LINE (D Line)
            {'name': 'Wilshire/Vermont', 'line': 'Purple', 'type': 'rail', 'lat': 34.058304, 'lon': -118.291870},
            {'name': 'Wilshire/Normandie', 'line': 'Purple', 'type': 'rail', 'lat': 34.062668, 'lon': -118.300146},
            {'name': 'Wilshire/Western', 'line': 'Purple', 'type': 'rail', 'lat': 34.062176, 'lon': -118.309090},
            
            # EXPO LINE (E Line) 
            {'name': 'Downtown Santa Monica', 'line': 'Expo', 'type': 'rail', 'lat': 34.013056, 'lon': -118.497222},
            {'name': '7th St/Metro Center', 'line': 'Red/Purple/Blue', 'type': 'rail', 'lat': 34.048653, 'lon': -118.259109},
            {'name': 'Grand/LATTC', 'line': 'Blue', 'type': 'rail', 'lat': 34.007605, 'lon': -118.268814},
            {'name': 'Washington', 'line': 'Blue', 'type': 'rail', 'lat': 33.989083, 'lon': -118.277023},
            {'name': 'Expo Park/USC', 'line': 'Expo', 'type': 'rail', 'lat': 34.018103, 'lon': -118.286814},
            {'name': 'Expo/Vermont', 'line': 'Expo', 'type': 'rail', 'lat': 34.018361, 'lon': -118.291750},
            {'name': 'Expo/Western', 'line': 'Expo', 'type': 'rail', 'lat': 34.018206, 'lon': -118.309097},
            {'name': 'Expo/Crenshaw', 'line': 'Expo', 'type': 'rail', 'lat': 34.018556, 'lon': -118.335556},
            {'name': 'Expo/La Brea', 'line': 'Expo', 'type': 'rail', 'lat': 34.025764, 'lon': -118.344247},
            {'name': 'Expo/La Cienega', 'line': 'Expo', 'type': 'rail', 'lat': 34.035069, 'lon': -118.376944},
            {'name': 'Expo/Bundy', 'line': 'Expo', 'type': 'rail', 'lat': 34.032889, 'lon': -118.454611},
            {'name': 'Expo/Sepulveda', 'line': 'Expo', 'type': 'rail', 'lat': 34.028833, 'lon': -118.473167},
            
            # GOLD LINE (L Line)
            {'name': 'Little Tokyo/Arts District', 'line': 'Gold', 'type': 'rail', 'lat': 34.050717, 'lon': -118.238251},
            {'name': 'Indiana', 'line': 'Gold', 'type': 'rail', 'lat': 34.057736, 'lon': -118.203156},
            {'name': 'Heritage Square', 'line': 'Gold', 'type': 'rail', 'lat': 34.104361, 'lon': -118.206322},
            {'name': 'Highland Park', 'line': 'Gold', 'type': 'rail', 'lat': 34.113431, 'lon': -118.210039},
        ]
    
    def _get_rapid_bus_stations(self) -> List[Dict]:
        """Get LA Metro rapid bus station definitions"""
        return [
            # ORANGE LINE (G Line) - Rapid Bus
            {'name': 'North Hollywood Orange', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.168710, 'lon': -118.376668},
            {'name': 'Van Nuys Orange', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.488889},
            {'name': 'Warner Center', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.601944},
        ]
    
    def _get_bus_intersections(self) -> List[Dict]:
        """Get major bus line intersection definitions"""
        return [
            {'name': 'Wilshire/Vermont', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.058304, 'lon': -118.291870},
            {'name': 'Hollywood/Highland', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.102403, 'lon': -118.338974},
            {'name': 'Sunset/Vine', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.098611, 'lon': -118.326667},
            {'name': 'Beverly/La Cienega', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.073889, 'lon': -118.376111},
            {'name': 'Sunset/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.095556, 'lon': -118.309167},
            {'name': 'Olympic/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.033889, 'lon': -118.309167},
            {'name': 'Washington/Crenshaw', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.039167, 'lon': -118.334722},
        ]
    
    def get_tier_config(self, tier: int) -> Dict:
        """Get configuration for specific TOC tier"""
        return self.tier_thresholds.get(tier, self.tier_thresholds[0])
    
    def get_all_stations(self) -> List[Dict]:
        """Get all stations combined"""
        all_stations = []
        all_stations.extend(self.station_config['rail_stations'])
        all_stations.extend(self.station_config['rapid_bus_stations'])
        all_stations.extend(self.station_config['bus_intersections'])
        return all_stations
    
    def export_config(self, filepath: str) -> None:
        """Export configuration to JSON file"""
        config_data = {
            'tier_thresholds': self.tier_thresholds,
            'stations': self.station_config
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config(self, filepath: str) -> None:
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        self.tier_thresholds = config_data['tier_thresholds']
        self.station_config = config_data['stations']


class TOCValidationConfig:
    """Configuration for TOC validation and testing"""
    
    @staticmethod
    def get_test_coordinates() -> List[Dict]:
        """Get test coordinates for validation"""
        return [
            {'name': 'Hollywood/Highland Station', 'lat': 34.102403, 'lon': -118.338974, 'expected_tier': 4},
            {'name': 'Union Station Plaza', 'lat': 34.056207, 'lon': -118.234468, 'expected_tier': 4},
            {'name': '7th St/Metro Center', 'lat': 34.048653, 'lon': -118.259109, 'expected_tier': 4},
            {'name': 'Near Hollywood/Highland (800 ft)', 'lat': 34.104403, 'lon': -118.338974, 'expected_tier': 3},
            {'name': 'Near Union Station (1200 ft)', 'lat': 34.058207, 'lon': -118.234468, 'expected_tier': 3},
            {'name': 'Mid-City near Expo line (1800 ft)', 'lat': 34.050000, 'lon': -118.340000, 'expected_tier': 2},
            {'name': 'West LA (far from transit)', 'lat': 34.060000, 'lon': -118.450000, 'expected_tier': 0},
            {'name': 'Beverly Hills (far from rail)', 'lat': 34.073620, 'lon': -118.400356, 'expected_tier': 0}
        ]
    
    @staticmethod
    def get_boundary_test_cases() -> List[Dict]:
        """Get boundary test cases for edge testing"""
        return [
            {'name': 'Exactly at station', 'offset_feet': 0, 'expected_tier': 4},
            {'name': '749 feet (just under Tier 4)', 'offset_feet': 749, 'expected_tier': 4},
            {'name': '751 feet (just over to Tier 3)', 'offset_feet': 751, 'expected_tier': 3},
            {'name': '1499 feet (just under Tier 3)', 'offset_feet': 1499, 'expected_tier': 3},
            {'name': '1501 feet (just over to Tier 2)', 'offset_feet': 1501, 'expected_tier': 2},
            {'name': '2639 feet (just under Tier 2)', 'offset_feet': 2639, 'expected_tier': 2},
            {'name': '2641 feet (beyond TOC)', 'offset_feet': 2641, 'expected_tier': 0},
        ]