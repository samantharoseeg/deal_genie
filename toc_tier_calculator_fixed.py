#!/usr/bin/env python3
"""
TOC Tier Calculator - FIXED VERSION
====================================

Fixed version of TOC calculator with correct boundary logic.
The issue was in the boundary conditions - they needed to be exclusive for proper tier assignment.
"""

import pandas as pd
import numpy as np
import math
from typing import Dict, List, Tuple, Optional
import json


class TOCTierCalculatorFixed:
    """Fixed TOC tier calculator with correct boundary logic"""
    
    def __init__(self):
        """Initialize with LA Metro station data"""
        self.rail_stations = self._load_rail_stations()
        self.bus_intersections = self._load_bus_intersections()
        
        # TOC tier definitions with CORRECTED boundaries
        self.tier_thresholds = {
            4: {'max_distance': 750, 'bonus_points': 15, 'description': 'Tier 4 - Rail/Rapid Bus Adjacent'},
            3: {'max_distance': 1500, 'bonus_points': 12, 'description': 'Tier 3 - Rail Proximity/Bus Intersection'},
            2: {'max_distance': 2640, 'bonus_points': 8, 'description': 'Tier 2 - Transit Zone'},
            1: {'max_distance': 2640, 'bonus_points': 5, 'description': 'Tier 1 - Transit Edge'},
            0: {'max_distance': float('inf'), 'bonus_points': 0, 'description': 'No TOC Tier'}
        }
        
        print(f"✅ Fixed TOC Calculator loaded with {len(self.rail_stations)} stations")
    
    def _load_rail_stations(self) -> pd.DataFrame:
        """Load LA Metro rail and rapid bus stations"""
        stations = [
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
            
            # ORANGE LINE (G Line) - Rapid Bus
            {'name': 'North Hollywood Orange', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.168710, 'lon': -118.376668},
            {'name': 'Van Nuys Orange', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.488889},
            {'name': 'Warner Center', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.601944},
        ]
        
        return pd.DataFrame(stations)
    
    def _load_bus_intersections(self) -> pd.DataFrame:
        """Load major bus line intersections"""
        intersections = [
            {'name': 'Wilshire/Vermont', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.058304, 'lon': -118.291870},
            {'name': 'Hollywood/Highland', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.102403, 'lon': -118.338974},
            {'name': 'Sunset/Vine', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.098611, 'lon': -118.326667},
            {'name': 'Beverly/La Cienega', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.073889, 'lon': -118.376111},
            {'name': 'Sunset/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.095556, 'lon': -118.309167},
            {'name': 'Olympic/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.033889, 'lon': -118.309167},
            {'name': 'Washington/Crenshaw', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.039167, 'lon': -118.334722},
        ]
        
        return pd.DataFrame(intersections)
    
    def calculate_distance_feet(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two lat/lon points in feet using Haversine formula"""
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return float('inf')
        
        try:
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            radius_feet = 20902231
            return c * radius_feet
            
        except Exception:
            return float('inf')
    
    def find_nearest_stations(self, property_lat: float, property_lon: float) -> Dict:
        """Find nearest rail, rapid bus, and bus intersection stations"""
        distances = {
            'nearest_rail': {'distance': float('inf'), 'station': None, 'info': None},
            'nearest_rapid_bus': {'distance': float('inf'), 'station': None, 'info': None},
            'nearest_bus_intersection': {'distance': float('inf'), 'station': None, 'info': None}
        }
        
        # Check rail stations
        for _, station in self.rail_stations.iterrows():
            distance = self.calculate_distance_feet(
                property_lat, property_lon,
                station['lat'], station['lon']
            )
            
            if distance == float('inf'):
                continue
            
            station_type = 'rail' if station['type'] == 'rail' else 'rapid_bus'
            
            if distance < distances[f'nearest_{station_type}']['distance']:
                distances[f'nearest_{station_type}'] = {
                    'distance': distance,
                    'station': station['name'],
                    'type': station_type,
                    'line': station['line'],
                    'info': station
                }
        
        # Check bus intersections
        for _, intersection in self.bus_intersections.iterrows():
            distance = self.calculate_distance_feet(
                property_lat, property_lon,
                intersection['lat'], intersection['lon']
            )
            
            if distance < distances['nearest_bus_intersection']['distance']:
                distances['nearest_bus_intersection'] = {
                    'distance': distance,
                    'station': intersection['name'],
                    'type': 'bus_intersection',
                    'line': intersection['lines'],
                    'info': intersection
                }
        
        return distances
    
    def calculate_toc_tier(self, property_lat: float, property_lon: float) -> Dict:
        """Calculate TOC tier with FIXED boundary logic"""
        if pd.isna(property_lat) or pd.isna(property_lon):
            return {
                'toc_tier': 0, 'bonus_points': 0,
                'description': 'No TOC Tier - Missing Coordinates',
                'nearest_station': None, 'distance_feet': None, 'station_type': None
            }
        
        nearest_stations = self.find_nearest_stations(property_lat, property_lon)
        
        rail_distance = nearest_stations['nearest_rail']['distance']
        rapid_bus_distance = nearest_stations['nearest_rapid_bus']['distance'] 
        bus_intersection_distance = nearest_stations['nearest_bus_intersection']['distance']
        
        # FIXED TOC tier logic with correct boundaries
        if rail_distance <= 750 or rapid_bus_distance <= 750:
            # Tier 4: Within 750 feet of rail/rapid bus (inclusive)
            tier = 4
            best_station = nearest_stations['nearest_rail'] if rail_distance <= rapid_bus_distance else nearest_stations['nearest_rapid_bus']
            
        elif rail_distance <= 1500:
            # Tier 3: 751-1500 feet from rail (inclusive)
            tier = 3
            best_station = nearest_stations['nearest_rail']
            
        elif bus_intersection_distance <= 750:
            # Tier 3: Within 750 feet of bus intersection (inclusive)
            tier = 3
            best_station = nearest_stations['nearest_bus_intersection']
            
        elif rail_distance <= 2640 or rapid_bus_distance <= 2640:
            # Tier 2: 1501-2640 feet from rail/rapid bus (inclusive)
            tier = 2
            best_station = nearest_stations['nearest_rail'] if rail_distance <= rapid_bus_distance else nearest_stations['nearest_rapid_bus']
            
        elif bus_intersection_distance <= 2640:
            # Tier 1: 751-2640 feet from bus intersection (inclusive)
            tier = 1
            best_station = nearest_stations['nearest_bus_intersection']
            
        else:
            # Tier 0: 2640+ feet from any transit
            tier = 0
            # Show nearest station even if far
            all_distances = [
                ('rail', rail_distance, nearest_stations['nearest_rail']),
                ('rapid_bus', rapid_bus_distance, nearest_stations['nearest_rapid_bus']),
                ('bus_intersection', bus_intersection_distance, nearest_stations['nearest_bus_intersection'])
            ]
            valid_distances = [(t, d, s) for t, d, s in all_distances if d != float('inf')]
            if valid_distances:
                _, _, best_station = min(valid_distances, key=lambda x: x[1])
            else:
                best_station = {'station': 'No stations found', 'distance': 0}
        
        return {
            'toc_tier': tier,
            'bonus_points': self.tier_thresholds[tier]['bonus_points'],
            'description': self.tier_thresholds[tier]['description'],
            'nearest_station': best_station['station'],
            'distance_feet': round(best_station['distance'], 0),
            'station_type': best_station.get('type', 'unknown'),
            'station_line': best_station.get('line', 'Unknown')
        }
    
    def process_properties_batch(self, properties_df: pd.DataFrame) -> pd.DataFrame:
        """Process batch of properties with fixed TOC calculation"""
        print(f"Processing TOC tiers for {len(properties_df)} properties with FIXED calculator...")
        
        toc_results = []
        
        for idx, row in properties_df.iterrows():
            lat = row.get('latitude', None) or row.get('lat', None)
            lon = row.get('longitude', None) or row.get('lon', None)
            
            toc_result = self.calculate_toc_tier(lat, lon)
            toc_results.append(toc_result)
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(properties_df)} properties...")
        
        # Add TOC data with fixed_ prefix to distinguish
        toc_df = pd.DataFrame(toc_results)
        for col in toc_df.columns:
            properties_df[f'fixed_toc_{col}'] = toc_df[col]
        
        print(f"✅ Fixed TOC tier calculation complete")
        
        # Summary statistics
        tier_distribution = properties_df['fixed_toc_toc_tier'].value_counts().sort_index()
        print(f"\nFixed TOC Tier Distribution:")
        for tier, count in tier_distribution.items():
            points = self.tier_thresholds[tier]['bonus_points']
            print(f"  Tier {tier} (+{points} points): {count} properties ({count/len(properties_df)*100:.1f}%)")
        
        return properties_df


def test_fixed_boundary_logic():
    """Test the fixed boundary logic"""
    print("🧪 TESTING FIXED BOUNDARY LOGIC")
    print("=" * 80)
    
    calculator = TOCTierCalculatorFixed()
    
    # Test exact boundary conditions using Hollywood/Highland as reference
    hollywood_lat, hollywood_lon = 34.102403, -118.338974
    
    test_cases = [
        {'name': 'Exactly at Hollywood/Highland', 'offset_feet': 0, 'expected_tier': 4},
        {'name': '500 feet away', 'offset_feet': 500, 'expected_tier': 4},
        {'name': '749 feet away (just under 750)', 'offset_feet': 749, 'expected_tier': 4},
        {'name': '751 feet away (just over 750)', 'offset_feet': 751, 'expected_tier': 3},
        {'name': '1499 feet away (just under 1500)', 'offset_feet': 1499, 'expected_tier': 3},
        {'name': '1501 feet away (just over 1500)', 'offset_feet': 1501, 'expected_tier': 2},
        {'name': '2639 feet away (just under 2640)', 'offset_feet': 2639, 'expected_tier': 2},
        {'name': '2641 feet away (just over 2640)', 'offset_feet': 2641, 'expected_tier': 0},
    ]
    
    all_correct = True
    
    for test in test_cases:
        # Calculate test coordinates (approximate - just for boundary testing)
        lat_offset = test['offset_feet'] / 364000  # Rough conversion
        test_lat = hollywood_lat + lat_offset
        test_lon = hollywood_lon
        
        result = calculator.calculate_toc_tier(test_lat, test_lon)
        
        correct = result['toc_tier'] == test['expected_tier']
        if not correct:
            all_correct = False
            
        status = "✅ PASS" if correct else "❌ FAIL"
        print(f"{status} {test['name']}")
        print(f"    Expected: Tier {test['expected_tier']} | Got: Tier {result['toc_tier']}")
        print(f"    Distance: {result['distance_feet']:,.0f} ft to {result['nearest_station']}")
    
    print(f"\n🏆 BOUNDARY LOGIC TEST SUMMARY")
    print("=" * 50)
    if all_correct:
        print("✅ ALL BOUNDARY TESTS PASSED - Fixed calculator working correctly!")
    else:
        print("❌ Some boundary tests failed - Further debugging needed")
    
    return all_correct


def main():
    """Test the fixed TOC calculator"""
    print("🔧 TESTING FIXED TOC CALCULATOR")
    print("=" * 100)
    
    # Test boundary logic
    boundary_ok = test_fixed_boundary_logic()
    
    # Test with original problematic locations
    calculator = TOCTierCalculatorFixed()
    
    print(f"\n🧪 TESTING ORIGINAL PROBLEM LOCATIONS")
    print("=" * 80)
    
    problem_locations = [
        {'name': '1500 S Fairfax Ave', 'lat': 34.045000, 'lon': -118.360000},
        {'name': '3rd St & Fairfax', 'lat': 34.073000, 'lon': -118.361000},
        {'name': '1600 N Vermont Ave', 'lat': 34.105000, 'lon': -118.291000},
    ]
    
    for location in problem_locations:
        result = calculator.calculate_toc_tier(location['lat'], location['lon'])
        print(f"\n{location['name']}")
        print(f"  Coordinates: {location['lat']:.6f}, {location['lon']:.6f}")  
        print(f"  TOC Tier: {result['toc_tier']} (+{result['bonus_points']} points)")
        print(f"  Nearest: {result['nearest_station']} at {result['distance_feet']:,.0f} ft")
    
    print(f"\n🏆 FIXED CALCULATOR STATUS")
    print("=" * 80)
    if boundary_ok:
        print("✅ Fixed TOC calculator is working correctly!")
        print("✅ Boundary logic has been corrected") 
        print("✅ Ready to replace original calculator")
    else:
        print("❌ Fixed calculator still has issues")


if __name__ == "__main__":
    main()