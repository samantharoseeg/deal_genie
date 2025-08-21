#!/usr/bin/env python3
"""
TOC Tier Calculator for DealGenie V4.3
======================================

Calculates Transit-Oriented Communities (TOC) tiers based on proximity to LA Metro stations
and assigns appropriate bonus points for development scoring.

Based on LA City Planning TOC guidelines:
- Tier 4: Within 750 feet of rail/rapid bus = +15 points
- Tier 3: 750-1500 feet from rail OR within 750ft of bus intersection = +12 points
- Tier 2: 1500-2640 feet from transit = +8 points
- Tier 1: Edge of half-mile radius (2640 feet) = +5 points
- Tier 0: Beyond half-mile = 0 points
"""

import pandas as pd
import numpy as np
import math
from typing import Dict, List, Tuple, Optional
import json


class TOCTierCalculator:
    """Calculate TOC tiers and bonus points based on transit proximity"""
    
    def __init__(self):
        """Initialize with LA Metro station data"""
        self.rail_stations = self._load_rail_stations()
        self.bus_intersections = self._load_bus_intersections()
        
        # TOC tier definitions (distance in feet)
        self.tier_thresholds = {
            4: {'max_distance': 750, 'bonus_points': 15, 'description': 'Tier 4 - Rail/Rapid Bus Adjacent'},
            3: {'max_distance': 1500, 'bonus_points': 12, 'description': 'Tier 3 - Rail Proximity/Bus Intersection'},
            2: {'max_distance': 2640, 'bonus_points': 8, 'description': 'Tier 2 - Transit Zone'},
            1: {'max_distance': 2640, 'bonus_points': 5, 'description': 'Tier 1 - Transit Edge'},
            0: {'max_distance': float('inf'), 'bonus_points': 0, 'description': 'No TOC Tier'}
        }
    
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
            
            # BLUE LINE (A Line)
            {'name': 'Downtown Santa Monica', 'line': 'Expo', 'type': 'rail', 'lat': 34.013056, 'lon': -118.497222},
            {'name': '7th St/Metro Center', 'line': 'Red/Purple/Blue', 'type': 'rail', 'lat': 34.048653, 'lon': -118.259109},
            {'name': 'Grand/LATTC', 'line': 'Blue', 'type': 'rail', 'lat': 34.007605, 'lon': -118.268814},
            {'name': 'San Pedro Street', 'line': 'Blue', 'type': 'rail', 'lat': 33.999825, 'lon': -118.273567},
            {'name': 'Washington', 'line': 'Blue', 'type': 'rail', 'lat': 33.989083, 'lon': -118.277023},
            {'name': 'Vernon', 'line': 'Blue', 'type': 'rail', 'lat': 33.987972, 'lon': -118.291534},
            {'name': 'Slauson', 'line': 'Blue', 'type': 'rail', 'lat': 33.988694, 'lon': -118.300621},
            {'name': 'Florence', 'line': 'Blue', 'type': 'rail', 'lat': 33.982597, 'lon': -118.327301},
            {'name': 'Firestone', 'line': 'Blue', 'type': 'rail', 'lat': 33.970600, 'lon': -118.326111},
            {'name': 'Compton', 'line': 'Blue', 'type': 'rail', 'lat': 33.896389, 'lon': -118.220278},
            {'name': 'Long Beach', 'line': 'Blue', 'type': 'rail', 'lat': 33.831139, 'lon': -118.208806},
            
            # GOLD LINE (L Line)
            {'name': 'Little Tokyo/Arts District', 'line': 'Gold', 'type': 'rail', 'lat': 34.050717, 'lon': -118.238251},
            {'name': 'Indiana', 'line': 'Gold', 'type': 'rail', 'lat': 34.057736, 'lon': -118.203156},
            {'name': 'Maravilla', 'line': 'Gold', 'type': 'rail', 'lat': 34.047800, 'lon': -118.172972},
            {'name': 'Montecito Heights', 'line': 'Gold', 'type': 'rail', 'lat': 34.079147, 'lon': -118.192581},
            {'name': 'Lincoln/Cypress', 'line': 'Gold', 'type': 'rail', 'lat': 34.090378, 'lon': -118.195406},
            {'name': 'Heritage Square', 'line': 'Gold', 'type': 'rail', 'lat': 34.104361, 'lon': -118.206322},
            {'name': 'Southwest Museum', 'line': 'Gold', 'type': 'rail', 'lat': 34.109753, 'lon': -118.209578},
            {'name': 'Highland Park', 'line': 'Gold', 'type': 'rail', 'lat': 34.113431, 'lon': -118.210039},
            {'name': 'South Pasadena', 'line': 'Gold', 'type': 'rail', 'lat': 34.116194, 'lon': -118.150556},
            {'name': 'Memorial Park', 'line': 'Gold', 'type': 'rail', 'lat': 34.131750, 'lon': -118.131139},
            {'name': 'Lake', 'line': 'Gold', 'type': 'rail', 'lat': 34.135353, 'lon': -118.126947},
            {'name': 'Allen', 'line': 'Gold', 'type': 'rail', 'lat': 34.140247, 'lon': -118.125889},
            {'name': 'Sierra Madre Villa', 'line': 'Gold', 'type': 'rail', 'lat': 34.161528, 'lon': -118.106778},
            
            # EXPO LINE (E Line)
            {'name': 'Expo Park/USC', 'line': 'Expo', 'type': 'rail', 'lat': 34.018103, 'lon': -118.286814},
            {'name': 'Expo/Vermont', 'line': 'Expo', 'type': 'rail', 'lat': 34.018361, 'lon': -118.291750},
            {'name': 'Expo/Western', 'line': 'Expo', 'type': 'rail', 'lat': 34.018206, 'lon': -118.309097},
            {'name': 'Expo/Crenshaw', 'line': 'Expo', 'type': 'rail', 'lat': 34.018556, 'lon': -118.335556},
            {'name': 'Farmdale', 'line': 'Expo', 'type': 'rail', 'lat': 34.018500, 'lon': -118.351472},
            {'name': 'Expo/La Brea', 'line': 'Expo', 'type': 'rail', 'lat': 34.025764, 'lon': -118.344247},
            {'name': 'Expo/La Cienega', 'line': 'Expo', 'type': 'rail', 'lat': 34.035069, 'lon': -118.376944},
            {'name': 'Expo/Bundy', 'line': 'Expo', 'type': 'rail', 'lat': 34.032889, 'lon': -118.454611},
            {'name': 'Expo/Sepulveda', 'line': 'Expo', 'type': 'rail', 'lat': 34.028833, 'lon': -118.473167},
            {'name': 'Santa Monica', 'line': 'Expo', 'type': 'rail', 'lat': 34.013056, 'lon': -118.497222},
            
            # ORANGE LINE (G Line) - Rapid Bus
            {'name': 'North Hollywood', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.168710, 'lon': -118.376668},
            {'name': 'Laurel Canyon', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.178639, 'lon': -118.396417},
            {'name': 'Valley College', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.180556, 'lon': -118.438889},
            {'name': 'Woodman', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.433056},
            {'name': 'Sepulveda', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.461944},
            {'name': 'Van Nuys', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.488889},
            {'name': 'Reseda', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.535278},
            {'name': 'Tampa', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.561944},
            {'name': 'Pierce College', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.588056},
            {'name': 'Canoga', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.597500},
            {'name': 'Warner Center', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.186389, 'lon': -118.601944},
            {'name': 'Chatsworth', 'line': 'Orange', 'type': 'rapid_bus', 'lat': 34.243056, 'lon': -118.628056},
            
            # SILVER LINE (J Line) - Rapid Bus
            {'name': 'El Monte Station', 'line': 'Silver', 'type': 'rapid_bus', 'lat': 34.072778, 'lon': -118.047500},
            {'name': 'Harbor Gateway Transit Center', 'line': 'Silver', 'type': 'rapid_bus', 'lat': 33.815556, 'lon': -118.285556},
            {'name': 'San Pedro', 'line': 'Silver', 'type': 'rapid_bus', 'lat': 33.736111, 'lon': -118.293056},
        ]
        
        return pd.DataFrame(stations)
    
    def _load_bus_intersections(self) -> pd.DataFrame:
        """Load major bus line intersections (2+ frequent routes)"""
        intersections = [
            # Major bus intersections throughout LA
            {'name': 'Wilshire/Vermont', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.058304, 'lon': -118.291870},
            {'name': 'Hollywood/Highland', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.102403, 'lon': -118.338974},
            {'name': 'Sunset/Vine', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.098611, 'lon': -118.326667},
            {'name': 'Beverly/La Cienega', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.073889, 'lon': -118.376111},
            {'name': 'Pico/Sepulveda', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.035278, 'lon': -118.472222},
            {'name': 'Venice/Lincoln', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 33.993889, 'lon': -118.464167},
            {'name': 'Crenshaw/Slauson', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 33.988333, 'lon': -118.334722},
            {'name': 'Vermont/Manchester', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 33.958889, 'lon': -118.291667},
            {'name': 'Van Nuys/Victory', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.187222, 'lon': -118.488889},
            {'name': 'Ventura/Sepulveda', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.157222, 'lon': -118.462778},
            {'name': 'Reseda/Nordhoff', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.235556, 'lon': -118.535278},
            {'name': 'Lankershim/Ventura', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.143889, 'lon': -118.389167},
            {'name': 'Sunset/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.095556, 'lon': -118.309167},
            {'name': 'Olympic/Western', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.033889, 'lon': -118.309167},
            {'name': 'Washington/Crenshaw', 'lines': 'Multiple', 'type': 'bus_intersection', 'lat': 34.039167, 'lon': -118.334722},
        ]
        
        return pd.DataFrame(intersections)
    
    def calculate_distance_feet(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two lat/lon points in feet using Haversine formula"""
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in feet (approximate)
        radius_feet = 20902231
        
        return c * radius_feet
    
    def find_nearest_stations(self, property_lat: float, property_lon: float) -> Dict:
        """Find nearest rail and bus stations to a property"""
        distances = {
            'nearest_rail': {'distance': float('inf'), 'station': None, 'type': None},
            'nearest_rapid_bus': {'distance': float('inf'), 'station': None, 'type': None},
            'nearest_bus_intersection': {'distance': float('inf'), 'station': None, 'type': None}
        }
        
        # Check rail stations
        for _, station in self.rail_stations.iterrows():
            if station['type'] == 'rail':
                distance = self.calculate_distance_feet(
                    property_lat, property_lon, 
                    station['lat'], station['lon']
                )
                if distance < distances['nearest_rail']['distance']:
                    distances['nearest_rail'] = {
                        'distance': distance,
                        'station': station['name'],
                        'type': 'rail',
                        'line': station['line']
                    }
            elif station['type'] == 'rapid_bus':
                distance = self.calculate_distance_feet(
                    property_lat, property_lon,
                    station['lat'], station['lon']
                )
                if distance < distances['nearest_rapid_bus']['distance']:
                    distances['nearest_rapid_bus'] = {
                        'distance': distance,
                        'station': station['name'],
                        'type': 'rapid_bus',
                        'line': station['line']
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
                    'line': intersection['lines']
                }
        
        return distances
    
    def calculate_toc_tier(self, property_lat: float, property_lon: float) -> Dict:
        """Calculate TOC tier and bonus points for a property"""
        if pd.isna(property_lat) or pd.isna(property_lon):
            return {
                'toc_tier': 0,
                'bonus_points': 0,
                'description': 'No TOC Tier - Missing Coordinates',
                'nearest_station': None,
                'distance_feet': None,
                'station_type': None
            }
        
        nearest_stations = self.find_nearest_stations(property_lat, property_lon)
        
        # Determine best TOC tier based on proximity rules
        rail_distance = nearest_stations['nearest_rail']['distance']
        rapid_bus_distance = nearest_stations['nearest_rapid_bus']['distance']
        bus_intersection_distance = nearest_stations['nearest_bus_intersection']['distance']
        
        # Apply TOC tier logic
        if rail_distance <= 750 or rapid_bus_distance <= 750:
            # Tier 4: Within 750 feet of rail/rapid bus
            tier = 4
            best_station = nearest_stations['nearest_rail'] if rail_distance <= rapid_bus_distance else nearest_stations['nearest_rapid_bus']
        elif rail_distance <= 1500:
            # Tier 3: 750-1500 feet from rail
            tier = 3
            best_station = nearest_stations['nearest_rail']
        elif bus_intersection_distance <= 750:
            # Tier 3: Within 750 feet of bus intersection
            tier = 3
            best_station = nearest_stations['nearest_bus_intersection']
        elif rail_distance <= 2640 or rapid_bus_distance <= 2640:
            # Tier 2: 1500-2640 feet from rail/rapid bus
            tier = 2
            best_station = nearest_stations['nearest_rail'] if rail_distance <= rapid_bus_distance else nearest_stations['nearest_rapid_bus']
        elif bus_intersection_distance <= 2640:
            # Tier 1: Edge of half-mile radius
            tier = 1
            best_station = nearest_stations['nearest_bus_intersection']
        else:
            # Tier 0: Beyond half-mile
            tier = 0
            best_station = nearest_stations['nearest_rail']  # Show nearest even if far
        
        return {
            'toc_tier': tier,
            'bonus_points': self.tier_thresholds[tier]['bonus_points'],
            'description': self.tier_thresholds[tier]['description'],
            'nearest_station': best_station['station'],
            'distance_feet': round(best_station['distance'], 0),
            'station_type': best_station['type'],
            'station_line': best_station.get('line', 'Unknown')
        }
    
    def process_properties_batch(self, properties_df: pd.DataFrame) -> pd.DataFrame:
        """Process a batch of properties and add TOC tier information"""
        print(f"Processing TOC tiers for {len(properties_df)} properties...")
        
        # Initialize new columns
        toc_results = []
        
        for idx, row in properties_df.iterrows():
            lat = row.get('latitude', None) or row.get('lat', None)
            lon = row.get('longitude', None) or row.get('lon', None)
            
            toc_result = self.calculate_toc_tier(lat, lon)
            toc_results.append(toc_result)
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(properties_df)} properties...")
        
        # Add TOC data to dataframe
        toc_df = pd.DataFrame(toc_results)
        for col in toc_df.columns:
            properties_df[f'toc_{col}'] = toc_df[col]
        
        print(f"✓ TOC tier calculation complete")
        
        # Summary statistics
        tier_distribution = properties_df['toc_toc_tier'].value_counts().sort_index()
        print(f"\nTOC Tier Distribution:")
        for tier, count in tier_distribution.items():
            points = self.tier_thresholds[tier]['bonus_points']
            print(f"  Tier {tier} (+{points} points): {count} properties ({count/len(properties_df)*100:.1f}%)")
        
        return properties_df
    
    def get_station_database(self) -> Dict:
        """Return the complete station database for reference"""
        return {
            'rail_stations': self.rail_stations.to_dict('records'),
            'bus_intersections': self.bus_intersections.to_dict('records'),
            'tier_thresholds': self.tier_thresholds
        }


def test_toc_calculator():
    """Test the TOC calculator with known locations"""
    print("Testing TOC Tier Calculator...")
    print("="*50)
    
    calculator = TOCTierCalculator()
    
    # Test properties at known locations
    test_properties = [
        {'name': 'Hollywood & Highland (should be Tier 4)', 'lat': 34.102403, 'lon': -118.338974},
        {'name': 'Property near Union Station', 'lat': 34.055000, 'lon': -118.235000},
        {'name': 'Property in Santa Monica', 'lat': 34.013000, 'lon': -118.497000},
        {'name': 'Property in West LA (far from transit)', 'lat': 34.050000, 'lon': -118.450000},
        {'name': 'Property near North Hollywood', 'lat': 34.168000, 'lon': -118.376000},
    ]
    
    for prop in test_properties:
        result = calculator.calculate_toc_tier(prop['lat'], prop['lon'])
        print(f"\n{prop['name']}")
        print(f"  TOC Tier: {result['toc_tier']} (+{result['bonus_points']} points)")
        print(f"  Description: {result['description']}")
        print(f"  Nearest Station: {result['nearest_station']} ({result['station_type']})")
        print(f"  Distance: {result['distance_feet']:,.0f} feet")
    
    print("\n✓ TOC Calculator test complete")


if __name__ == "__main__":
    test_toc_calculator()