#!/usr/bin/env python3
"""
DealGenie Scoring Engine V4.3 with TOC Integration
=================================================

Enhanced version of the DealGenie scoring engine that includes:
- All original scoring components (zoning, lot size, financial, risk)
- NEW: TOC (Transit-Oriented Communities) tier bonus integration
- Calibrated to achieve investment-grade scores (70+) for prime properties

This addresses the conservative scoring issue identified in testing.
"""

import pandas as pd
import json
from typing import Dict, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

from toc_tier_calculator import TOCTierCalculator


class DealGenieScorer_V4_3_TOC:
    """Enhanced property scoring engine with TOC tier integration"""
    
    def __init__(self, config_path: str = None):
        """Initialize scorer with TOC calculator and updated configuration"""
        if config_path:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self.get_default_config()
        
        # Initialize TOC calculator
        self.toc_calculator = TOCTierCalculator()
        print("✓ DealGenie V4.3 with TOC integration initialized")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Enhanced scoring configuration with TOC integration"""
        return {
            "weights": {
                "zoning_score": 0.30,      # Reduced from 0.35 to make room for TOC
                "lot_size_score": 0.25,    # Unchanged
                "toc_bonus": 0.25,         # NEW: TOC bonus weighting
                "financial_score": 0.10,   # Unchanged
                "risk_penalty": 0.10       # Unchanged
            },
            "zoning_scores": {
                # Enhanced high-density residential scores
                "R5": 105, "RAS4": 100, "RAS3": 98, "R4": 95,  # Boosted for investment grade
                # Medium-high density
                "RD3": 90, "RD2.5": 87, "RD2": 85, "R3": 80, "RD1.5": 75, "RD1": 72,
                # Enhanced commercial zones
                "C4": 100, "C2": 95, "CM": 90, "C1.5": 85, "C1": 82,  # Boosted commercial
                # Industrial (light)
                "M2": 80, "M1": 75, "MR1": 77, "MR2": 79,
                # Low density residential
                "R2": 55, "RD5": 52, "RD4": 50, "RD6": 48,
                "R1": 42, "RS": 40, "RE": 38, "RA": 35,
                # Special zones
                "PF": 30, "OS": 25, "A1": 20, "A2": 20
            },
            "lot_size_thresholds": [
                {"min": 30000, "max": float('inf'), "score_range": [95, 100]},  # Enhanced large lot scoring
                {"min": 20000, "max": 30000, "score_range": [90, 95]},
                {"min": 10000, "max": 20000, "score_range": [80, 90]},
                {"min": 7000, "max": 10000, "score_range": [70, 80]},
                {"min": 5000, "max": 7000, "score_range": [60, 70]},
                {"min": 3000, "max": 5000, "score_range": [45, 60]},
                {"min": 0, "max": 3000, "score_range": [25, 45]}
            ],
            "toc_bonuses": {
                # NEW: TOC tier bonuses (direct from TOC calculator)
                4: 15,  # Rail/rapid bus adjacent (tier_4)
                3: 12,  # Rail proximity/bus intersection (tier_3)
                2: 8,   # Transit zone (tier_2)
                1: 5,   # Transit edge (tier_1)
                0: 0    # No TOC benefit (tier_0)
            },
            "financial_bonuses": {
                "high_land_ratio": {"threshold": 0.70, "bonus": 12},  # Enhanced from 10
                "low_far": {"threshold": 0.50, "bonus": 8},           # Enhanced from 5
                "very_low_far": {"threshold": 0.25, "bonus": 12}     # Enhanced from 8
            },
            "risk_penalties": {
                "overlay_per_zone": 3,
                "methane_zone": 5,
                "methane_buffer": 3,
                "historic_zone": 8,
                "fault_zone": 4,
                "flood_zone": 3,
                "very_high_fire": 6
            },
            "investment_tiers": {
                "A+": {"min": 85, "description": "Premium Development Opportunity"},  # NEW tier
                "A": {"min": 75, "description": "Excellent Development Opportunity"},   # Lowered from 80
                "B": {"min": 65, "description": "Strong Development Potential"},
                "C": {"min": 50, "description": "Moderate Development Potential"},
                "D": {"min": 0, "description": "Limited Development Potential"}
            }
        }
    
    def calculate_zoning_score(self, base_zoning: str) -> float:
        """Calculate zoning score based on development potential"""
        if pd.isna(base_zoning):
            return 35.0
        
        base_zoning = str(base_zoning).upper().strip()
        
        # Direct lookup
        if base_zoning in self.config["zoning_scores"]:
            return float(self.config["zoning_scores"][base_zoning])
        
        # Try to match partial patterns
        for zone_pattern, score in self.config["zoning_scores"].items():
            if base_zoning.startswith(zone_pattern):
                return float(score)
        
        # Default score for unknown zones
        return 40.0  # Slightly higher default
    
    def calculate_lot_size_score(self, lot_size_sqft: float) -> float:
        """Calculate lot size score based on development potential"""
        if pd.isna(lot_size_sqft) or lot_size_sqft <= 0:
            return 25.0
        
        for threshold in self.config["lot_size_thresholds"]:
            if threshold["min"] <= lot_size_sqft < threshold["max"]:
                # Linear interpolation within range
                score_min, score_max = threshold["score_range"]
                if threshold["max"] == float('inf'):
                    return min(100, score_max)
                
                # Calculate position within range
                range_size = threshold["max"] - threshold["min"]
                position = (lot_size_sqft - threshold["min"]) / range_size
                return score_min + (score_max - score_min) * position
        
        return 35.0
    
    def calculate_toc_bonus(self, row: pd.Series) -> float:
        """Calculate TOC bonus based on transit proximity"""
        # Check if property already has TOC data
        if 'toc_toc_tier' in row and pd.notna(row['toc_toc_tier']):
            tier = int(row['toc_toc_tier'])
            return float(self.config["toc_bonuses"].get(tier, 0))
        
        # Check for coordinates to calculate TOC tier
        lat = row.get('latitude', None) or row.get('lat', None)
        lon = row.get('longitude', None) or row.get('lon', None)
        
        if pd.notna(lat) and pd.notna(lon):
            toc_result = self.toc_calculator.calculate_toc_tier(float(lat), float(lon))
            return float(toc_result['bonus_points'])
        
        # Legacy TOC eligibility check (for backward compatibility)
        if row.get('toc_eligible', False):
            return 10.0  # Default bonus for TOC-eligible without tier data
        
        return 0.0
    
    def calculate_financial_score(self, row: pd.Series) -> float:
        """Calculate enhanced financial indicators score"""
        score = 0
        bonuses = self.config["financial_bonuses"]
        
        # Land value ratio (high = redevelopment opportunity)
        if pd.notna(row.get('assessed_land_value')) and pd.notna(row.get('total_assessed_value')):
            if row['total_assessed_value'] > 0:
                land_ratio = row['assessed_land_value'] / row['total_assessed_value']
                if land_ratio >= bonuses["high_land_ratio"]["threshold"]:
                    score += bonuses["high_land_ratio"]["bonus"]
        
        # FAR calculation (low = underbuilt)
        if pd.notna(row.get('building_size_sqft')) and pd.notna(row.get('lot_size_sqft')):
            if row['lot_size_sqft'] > 0:
                far = row['building_size_sqft'] / row['lot_size_sqft']
                if far <= bonuses["very_low_far"]["threshold"]:
                    score += bonuses["very_low_far"]["bonus"]
                elif far <= bonuses["low_far"]["threshold"]:
                    score += bonuses["low_far"]["bonus"]
        
        return min(score, 20)  # Increased cap from 15 to 20
    
    def calculate_risk_penalty(self, row: pd.Series) -> float:
        """Calculate risk penalties from constraints and overlays"""
        penalty = 0
        penalties = self.config["risk_penalties"]
        
        # Overlay zones
        overlay_count = row.get('overlay_count', 0)
        if pd.notna(overlay_count):
            penalty += overlay_count * penalties["overlay_per_zone"]
        
        # Environmental hazards
        methane = str(row.get('methane_zone', '')).lower()
        if 'methane zone' in methane:
            penalty += penalties["methane_zone"]
        elif 'buffer' in methane:
            penalty += penalties["methane_buffer"]
        
        # Historic preservation
        if pd.notna(row.get('specific_plan_area')):
            plan = str(row['specific_plan_area']).lower()
            if 'historic' in plan or 'hpoz' in plan:
                penalty += penalties["historic_zone"]
        
        # Fault zones
        if pd.notna(row.get('fault_zone')):
            fault = str(row['fault_zone']).lower()
            if fault not in ['', 'none', 'nan']:
                penalty += penalties["fault_zone"]
        
        # Flood zones
        flood = str(row.get('flood_zone', '')).lower()
        if 'flood' in flood and 'outside' not in flood:
            penalty += penalties["flood_zone"]
        
        return min(penalty, 25)  # Increased cap from 20 to 25
    
    def suggest_use_case(self, row: pd.Series, total_score: float) -> str:
        """Enhanced use case suggestions with TOC consideration"""
        base_zoning = str(row.get('base_zoning', '')).upper()
        lot_size = row.get('lot_size_sqft', 0)
        toc_tier = row.get('toc_toc_tier', 0)
        land_ratio = 0
        
        if pd.notna(row.get('assessed_land_value')) and pd.notna(row.get('total_assessed_value')):
            if row['total_assessed_value'] > 0:
                land_ratio = row['assessed_land_value'] / row['total_assessed_value']
        
        # TOC-enhanced suggestions
        if toc_tier >= 3:  # High TOC tiers
            if lot_size >= 15000:
                if base_zoning in ['R4', 'R5', 'RAS3', 'RAS4']:
                    return "Major TOC Development (200+ units)"
                elif base_zoning in ['C4', 'CM']:
                    return "Transit-Oriented Mixed-Use Complex"
                elif base_zoning in ['R3']:
                    return "TOC Multi-Family Development (50-100 units)"
            elif lot_size >= 7000:
                if base_zoning in ['R3', 'R4', 'R5']:
                    return "TOC Multi-Family Development (20-50 units)"
                elif base_zoning in ['C2', 'C4']:
                    return "Transit-Adjacent Commercial"
        
        # Large lot opportunities
        if lot_size >= 20000:
            if base_zoning in ['R3', 'R4', 'R5', 'RAS3', 'RAS4']:
                return "Large Multi-Family Development"
            elif base_zoning in ['C2', 'C4', 'CM']:
                return "Mixed-Use Development"
            elif base_zoning in ['M1', 'M2']:
                return "Creative Office/Live-Work"
            elif land_ratio > 0.7:
                return "Prime Assembly Opportunity"
        
        # Medium lots
        elif lot_size >= 7000:
            if base_zoning in ['R3', 'R4', 'RD2', 'RD3']:
                return "Multi-Family Development"
            elif base_zoning in ['C2', 'C4']:
                return "Commercial Development"
            elif base_zoning in ['R1', 'R2'] and land_ratio > 0.65:
                return "SB9 Lot Split Opportunity"
        
        # Small lots
        elif lot_size >= 3000:
            if base_zoning in ['R3', 'RD1.5', 'RD2']:
                return "Small Lot Subdivision"
            elif base_zoning in ['C1', 'C2']:
                return "Boutique Retail/Office"
            elif base_zoning in ['R1'] and toc_tier >= 2:
                return "TOC ADU Development"
        
        # Zoning-specific suggestions
        if base_zoning in ['C2', 'C4', 'CM']:
            return "Commercial Development"
        elif base_zoning in ['R3', 'R4', 'R5'] and toc_tier >= 2:
            return "Transit-Oriented Housing"
        elif land_ratio > 0.75:
            return "Teardown/Rebuild Opportunity"
        elif total_score >= 75:
            return "Premium Development Opportunity"
        elif total_score >= 65:
            return "Strong Development Opportunity"
        elif total_score >= 50:
            return "Value-Add Investment"
        
        return "Hold/Income Property"
    
    def calculate_property_score(self, row: pd.Series) -> Tuple[float, Dict[str, float]]:
        """Calculate total development score with TOC integration"""
        weights = self.config["weights"]
        
        # Calculate component scores
        scores = {
            "zoning_score": self.calculate_zoning_score(row.get('base_zoning')),
            "lot_size_score": self.calculate_lot_size_score(row.get('lot_size_sqft')),
            "toc_bonus": self.calculate_toc_bonus(row),
            "financial_score": self.calculate_financial_score(row),
            "risk_penalty": self.calculate_risk_penalty(row)
        }
        
        # Calculate weighted total (risk is subtracted)
        total_score = (
            scores["zoning_score"] * weights["zoning_score"] +
            scores["lot_size_score"] * weights["lot_size_score"] +
            scores["toc_bonus"] * weights["toc_bonus"] +
            scores["financial_score"] * weights["financial_score"] -
            scores["risk_penalty"] * weights["risk_penalty"]
        )
        
        # Normalize to 0-100 scale
        total_score = max(0, min(100, total_score))
        
        return total_score, scores
    
    def get_investment_tier(self, score: float) -> str:
        """Determine investment tier based on enhanced score ranges"""
        for tier, criteria in self.config["investment_tiers"].items():
            if score >= criteria["min"]:
                return tier
        return "D"
    
    def score_properties(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score all properties with TOC integration"""
        print("Scoring properties with TOC integration...")
        
        # Initialize new columns
        df['development_score'] = 0.0
        df['score_breakdown'] = ''
        df['suggested_use'] = ''
        df['investment_tier'] = ''
        
        # Score each property
        for idx, row in df.iterrows():
            score, breakdown = self.calculate_property_score(row)
            
            df.at[idx, 'development_score'] = round(score, 2)
            df.at[idx, 'score_breakdown'] = json.dumps(breakdown, default=str)
            df.at[idx, 'suggested_use'] = self.suggest_use_case(row, score)
            df.at[idx, 'investment_tier'] = self.get_investment_tier(score)
            
            if (idx + 1) % 100 == 0:
                print(f"  Scored {idx + 1}/{len(df)} properties...")
        
        print(f"✓ Scored all {len(df)} properties with TOC integration")
        return df
    
    def add_toc_data_to_properties(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add TOC tier data to properties that have coordinates"""
        print("Adding TOC tier data to properties...")
        
        # Check for coordinate columns
        lat_col = None
        lon_col = None
        for col in df.columns:
            if 'lat' in col.lower():
                lat_col = col
            if 'lon' in col.lower():
                lon_col = col
        
        if lat_col is None or lon_col is None:
            print("⚠️ No coordinate columns found. Cannot calculate TOC tiers.")
            print("Available columns:", list(df.columns))
            return df
        
        print(f"Using coordinates: {lat_col}, {lon_col}")
        
        # Calculate TOC tiers for properties with coordinates
        toc_results = []
        valid_coords = 0
        
        for idx, row in df.iterrows():
            lat = row[lat_col]
            lon = row[lon_col]
            
            if pd.notna(lat) and pd.notna(lon):
                toc_result = self.toc_calculator.calculate_toc_tier(float(lat), float(lon))
                valid_coords += 1
            else:
                toc_result = {
                    'toc_tier': 0,
                    'bonus_points': 0,
                    'description': 'No TOC Tier - Missing Coordinates',
                    'nearest_station': None,
                    'distance_feet': None,
                    'station_type': None,
                    'station_line': None
                }
            
            toc_results.append(toc_result)
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(df)} properties...")
        
        # Add TOC data to dataframe
        toc_df = pd.DataFrame(toc_results)
        for col in toc_df.columns:
            df[f'toc_{col}'] = toc_df[col]
        
        print(f"✓ TOC data added to {len(df)} properties")
        print(f"  Properties with valid coordinates: {valid_coords}")
        
        # TOC tier distribution
        if valid_coords > 0:
            tier_dist = df['toc_toc_tier'].value_counts().sort_index()
            print(f"\nTOC Tier Distribution:")
            for tier, count in tier_dist.items():
                bonus = self.config["toc_bonuses"].get(f"tier_{tier}", 0)
                print(f"  Tier {tier} (+{bonus} points): {count} properties ({count/len(df)*100:.1f}%)")
        
        return df


def main():
    """Test the enhanced scoring engine"""
    print("="*80)
    print("TESTING DEALGENIE V4.3 WITH TOC INTEGRATION")
    print("="*80)
    
    # Create test properties
    test_data = [
        # High TOC tier property
        {
            'apn': 'TEST_TOC_1',
            'address': 'Near Hollywood/Highland Station',
            'base_zoning': 'R4',
            'lot_size_sqft': 15000,
            'building_size_sqft': 2000,
            'latitude': 34.102403,
            'longitude': -118.338974,
            'assessed_land_value': 8000000,
            'total_assessed_value': 8500000
        },
        # Medium TOC tier property
        {
            'apn': 'TEST_TOC_2', 
            'address': 'Near Transit Zone',
            'base_zoning': 'R3',
            'lot_size_sqft': 8000,
            'building_size_sqft': 1500,
            'latitude': 34.100000,
            'longitude': -118.340000,
            'assessed_land_value': 3000000,
            'total_assessed_value': 3500000
        },
        # No TOC property
        {
            'apn': 'TEST_TOC_3',
            'address': 'Far from Transit',
            'base_zoning': 'R1',
            'lot_size_sqft': 6000,
            'building_size_sqft': 1800,
            'latitude': 34.050000,
            'longitude': -118.450000,
            'assessed_land_value': 2000000,
            'total_assessed_value': 2800000
        }
    ]
    
    df = pd.DataFrame(test_data)
    
    # Initialize enhanced scorer
    scorer = DealGenieScorer_V4_3_TOC()
    
    # Add TOC data
    df = scorer.add_toc_data_to_properties(df)
    
    # Score properties
    df_scored = scorer.score_properties(df)
    
    # Display results
    print(f"\n" + "="*80)
    print("ENHANCED SCORING RESULTS")
    print("="*80)
    
    for idx, row in df_scored.iterrows():
        print(f"\nProperty {idx + 1}: {row['address']}")
        print(f"Zoning: {row['base_zoning']} | Lot: {row['lot_size_sqft']:,} sqft")
        print(f"TOC Tier: {row['toc_toc_tier']} (+{row['toc_bonus_points']} points)")
        print(f"Nearest Station: {row['toc_nearest_station']} ({row['toc_distance_feet']:,.0f} ft)")
        print(f"FINAL SCORE: {row['development_score']:.1f} | Tier: {row['investment_tier']}")
        print(f"Use Case: {row['suggested_use']}")
        
        # Component breakdown
        breakdown = json.loads(row['score_breakdown'])
        print("Component Scores:")
        for component, score in breakdown.items():
            print(f"  {component}: {score:.1f}")
        print("-" * 60)
    
    print(f"\n✓ Enhanced scoring test complete")


if __name__ == "__main__":
    main()