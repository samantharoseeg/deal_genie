#!/usr/bin/env python3
"""
Debug TOC Calculator Issues
============================

Debug and fix the fundamental issues with the TOC calculator that were identified
in validation testing.
"""

import pandas as pd
import numpy as np
import math
import json
from typing import Dict, List, Tuple, Optional

class DebugTOCCalculator:
    """Debug version of TOC calculator with extensive logging"""
    
    def __init__(self):
        """Initialize with debugging enabled"""
        self.rail_stations = self._load_rail_stations()
        self.bus_intersections = self._load_bus_intersections()
        self.tier_thresholds = {
            4: {'max_distance': 750, 'bonus_points': 15},
            3: {'max_distance': 1500, 'bonus_points': 12},
            2: {'max_distance': 2640, 'bonus_points': 8},
            1: {'max_distance': 2640, 'bonus_points': 5},
            0: {'max_distance': float('inf'), 'bonus_points': 0}
        }
        
        print(f"✅ Loaded {len(self.rail_stations)} stations and {len(self.bus_intersections)} intersections")
    
    def _load_rail_stations(self) -> pd.DataFrame:
        """Load corrected station data"""
        stations = [
            # Core stations that should always work
            {'name': 'Hollywood/Highland', 'line': 'Red', 'type': 'rail', 'lat': 34.102403, 'lon': -118.338974},
            {'name': 'Union Station', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.056207, 'lon': -118.234468},
            {'name': '7th St/Metro Center', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.048653, 'lon': -118.259109},
            {'name': 'Westlake/MacArthur Park', 'line': 'Red/Purple', 'type': 'rail', 'lat': 34.058205, 'lon': -118.277092},
            {'name': 'Hollywood/Western', 'line': 'Red', 'type': 'rail', 'lat': 34.101707, 'lon': -118.309471},
            {'name': 'North Hollywood', 'line': 'Red', 'type': 'rail', 'lat': 34.168710, 'lon': -118.376668},
            
            # Expo Line
            {'name': 'Expo/La Cienega', 'line': 'Expo', 'type': 'rail', 'lat': 34.035069, 'lon': -118.376944},
            {'name': 'Expo/Bundy', 'line': 'Expo', 'type': 'rail', 'lat': 34.032889, 'lon': -118.454611},
            {'name': 'Expo/Crenshaw', 'line': 'Expo', 'type': 'rail', 'lat': 34.018556, 'lon': -118.335556},
            {'name': 'Expo/La Brea', 'line': 'Expo', 'type': 'rail', 'lat': 34.025764, 'lon': -118.344247},
            {'name': 'Expo Park/USC', 'line': 'Expo', 'type': 'rail', 'lat': 34.018103, 'lon': -118.286814},
            
            # Purple Line
            {'name': 'Wilshire/Western', 'line': 'Purple', 'type': 'rail', 'lat': 34.062176, 'lon': -118.309090},
            {'name': 'Wilshire/Vermont', 'line': 'Purple', 'type': 'rail', 'lat': 34.058304, 'lon': -118.291870},
            
            # Gold Line
            {'name': 'Heritage Square', 'line': 'Gold', 'type': 'rail', 'lat': 34.104361, 'lon': -118.206322},
            {'name': 'Highland Park', 'line': 'Gold', 'type': 'rail', 'lat': 34.113431, 'lon': -118.210039},
            
            # Major rapid bus stations
            {'name': 'North Hollywood Orange', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.168710, 'lon': -118.376668},
        ]
        
        return pd.DataFrame(stations)
    
    def _load_bus_intersections(self) -> pd.DataFrame:
        """Load major bus intersections"""
        intersections = [
            {'name': 'Wilshire/Vermont', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.058304, 'lon': -118.291870},
            {'name': 'Hollywood/Highland', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.102403, 'lon': -118.338974},
            {'name': 'Sunset/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.095556, 'lon': -118.309167},
            {'name': 'Olympic/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.033889, 'lon': -118.309167},
        ]
        
        return pd.DataFrame(intersections)
    
    def calculate_distance_feet(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance with debugging"""
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            print(f"    ❌ Distance calc failed: NaN coordinates")
            return float('inf')
        
        try:
            # Haversine formula
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Radius of Earth in feet
            radius_feet = 20902231
            distance = c * radius_feet
            
            return distance
            
        except Exception as e:
            print(f"    ❌ Distance calculation error: {e}")
            return float('inf')
    
    def debug_calculate_toc_tier(self, property_lat: float, property_lon: float, verbose: bool = True) -> Dict:
        """Calculate TOC tier with extensive debugging"""
        if verbose:
            print(f"\n🔍 DEBUG: Calculating TOC for ({property_lat:.6f}, {property_lon:.6f})")
        
        if pd.isna(property_lat) or pd.isna(property_lon):
            if verbose:
                print("    ❌ Missing coordinates")
            return {
                'toc_tier': 0, 'bonus_points': 0, 'description': 'No coordinates',
                'nearest_station': None, 'distance_feet': None, 'debug': 'missing_coords'
            }
        
        # Find nearest stations with debugging
        nearest_distances = {
            'rail': {'distance': float('inf'), 'station': None, 'info': None},
            'rapid_bus': {'distance': float('inf'), 'station': None, 'info': None},
            'bus_intersection': {'distance': float('inf'), 'station': None, 'info': None}
        }
        
        # Check rail stations
        if verbose:
            print(f"    Checking {len(self.rail_stations)} stations...")
        
        for idx, station in self.rail_stations.iterrows():
            distance = self.calculate_distance_feet(
                property_lat, property_lon,
                station['lat'], station['lon']
            )
            
            if distance == float('inf'):
                continue
            
            station_type = 'rail' if station['type'] == 'rail' else 'rapid_bus'
            
            if distance < nearest_distances[station_type]['distance']:
                nearest_distances[station_type] = {
                    'distance': distance,
                    'station': station['name'],
                    'info': station
                }
                
                if verbose and distance < 5000:  # Only show nearby stations
                    print(f"      Found {station['name']}: {distance:,.0f} ft ({station['type']})")
        
        # Check bus intersections
        for idx, intersection in self.bus_intersections.iterrows():
            distance = self.calculate_distance_feet(
                property_lat, property_lon,
                intersection['lat'], intersection['lon']
            )
            
            if distance < nearest_distances['bus_intersection']['distance']:
                nearest_distances['bus_intersection'] = {
                    'distance': distance,
                    'station': intersection['name'],
                    'info': intersection
                }
        
        # Apply TOC tier logic with debugging
        rail_dist = nearest_distances['rail']['distance']
        rapid_bus_dist = nearest_distances['rapid_bus']['distance']
        bus_int_dist = nearest_distances['bus_intersection']['distance']
        
        if verbose:
            print(f"    Nearest rail: {nearest_distances['rail']['station']} at {rail_dist:,.0f} ft")
            print(f"    Nearest rapid bus: {nearest_distances['rapid_bus']['station']} at {rapid_bus_dist:,.0f} ft")
            print(f"    Nearest bus intersection: {nearest_distances['bus_intersection']['station']} at {bus_int_dist:,.0f} ft")
        
        # Determine tier
        if rail_dist <= 750 or rapid_bus_dist <= 750:
            tier = 4
            best_station = nearest_distances['rail'] if rail_dist <= rapid_bus_dist else nearest_distances['rapid_bus']
            reason = f"Within 750ft of rail/rapid bus"
        elif rail_dist <= 1500:
            tier = 3
            best_station = nearest_distances['rail']
            reason = f"Within 1500ft of rail"
        elif bus_int_dist <= 750:
            tier = 3
            best_station = nearest_distances['bus_intersection']
            reason = f"Within 750ft of bus intersection"
        elif rail_dist <= 2640 or rapid_bus_dist <= 2640:
            tier = 2
            best_station = nearest_distances['rail'] if rail_dist <= rapid_bus_dist else nearest_distances['rapid_bus']
            reason = f"Within half-mile of rail/rapid bus"
        elif bus_int_dist <= 2640:
            tier = 1
            best_station = nearest_distances['bus_intersection']
            reason = f"Within half-mile of bus intersection"
        else:
            tier = 0
            # Show nearest station even if far
            all_distances = [(k, v['distance'], v) for k, v in nearest_distances.items() if v['distance'] != float('inf')]
            if all_distances:
                nearest_type, nearest_dist, best_station = min(all_distances, key=lambda x: x[1])
            else:
                best_station = {'station': 'No stations found', 'distance': 0}
            reason = f"Beyond half-mile from transit"
        
        if verbose:
            print(f"    ✅ Result: Tier {tier} ({reason})")
            print(f"    Station: {best_station['station']} at {best_station['distance']:,.0f} ft")
        
        return {
            'toc_tier': tier,
            'bonus_points': self.tier_thresholds[tier]['bonus_points'],
            'description': reason,
            'nearest_station': best_station['station'],
            'distance_feet': round(best_station['distance'], 0),
            'debug_info': {
                'rail_distance': rail_dist,
                'rapid_bus_distance': rapid_bus_dist,
                'bus_intersection_distance': bus_int_dist,
                'decision_reason': reason
            }
        }
    
    def test_problematic_locations(self):
        """Test the locations that were failing"""
        print("🧪 TESTING PROBLEMATIC LOCATIONS")
        print("=" * 80)
        
        problem_locations = [
            {'name': '1500 S Fairfax Ave (should be Tier 2)', 'lat': 34.045000, 'lon': -118.360000},
            {'name': '3rd St & Fairfax (should be Tier 3)', 'lat': 34.073000, 'lon': -118.361000},
            {'name': '1600 N Vermont Ave (should be Tier 2)', 'lat': 34.105000, 'lon': -118.291000},
            {'name': '5600 W Pico Blvd (should be Tier 3)', 'lat': 34.047000, 'lon': -118.350000},
        ]
        
        for location in problem_locations:
            print(f"\n{'='*60}")
            print(f"Testing: {location['name']}")
            print(f"Coordinates: {location['lat']:.6f}, {location['lon']:.6f}")
            
            result = self.debug_calculate_toc_tier(location['lat'], location['lon'], verbose=True)
            
            print(f"Final result: Tier {result['toc_tier']} (+{result['bonus_points']} points)")


def main():
    """Run TOC calculator debugging"""
    print("🔧 DEBUGGING TOC CALCULATOR ISSUES")
    print("=" * 100)
    
    debugger = DebugTOCCalculator()
    debugger.test_problematic_locations()
    
    print(f"\n" + "="*100)
    print("DEBUGGING COMPLETE")
    print("="*100)


if __name__ == "__main__":
    main()