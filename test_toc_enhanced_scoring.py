#!/usr/bin/env python3
"""
Test TOC-Enhanced DealGenie V4.3 on 1,000 Property Sample
=========================================================

This script:
1. Loads the 1,000 diverse property sample
2. Adds estimated coordinates based on ZIP codes
3. Runs both original and TOC-enhanced scoring
4. Generates before/after comparison report
5. Identifies properties reaching investment grade (70+)
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from dealgenie_scoring_engine import DealGenieScorer
from dealgenie_scoring_engine_v4_3_toc import DealGenieScorer_V4_3_TOC


class TOCTestRunner:
    """Test runner for TOC-enhanced scoring comparison"""
    
    def __init__(self):
        """Initialize scorers"""
        self.original_scorer = DealGenieScorer()
        self.enhanced_scorer = DealGenieScorer_V4_3_TOC()
        
        # ZIP code center coordinates (approximate)
        self.zip_coordinates = {
            90001: (33.973, -118.248), 90002: (33.949, -118.248), 90003: (33.964, -118.272),
            90004: (34.077, -118.309), 90005: (34.059, -118.309), 90006: (34.048, -118.291),
            90007: (34.027, -118.287), 90008: (34.011, -118.341), 90010: (34.062, -118.300),
            90011: (33.996, -118.258), 90012: (34.066, -118.238), 90013: (34.040, -118.250),
            90014: (34.042, -118.255), 90015: (34.040, -118.266), 90016: (34.039, -118.341),
            90017: (34.052, -118.257), 90018: (34.016, -118.308), 90019: (34.043, -118.343),
            90020: (34.064, -118.309), 90021: (34.033, -118.238), 90022: (34.019, -118.215),
            90023: (34.017, -118.229), 90024: (34.062, -118.442), 90025: (34.043, -118.431),
            90026: (34.090, -118.261), 90027: (34.107, -118.287), 90028: (34.101, -118.329),
            90029: (34.089, -118.288), 90031: (34.064, -118.210), 90032: (34.063, -118.181),
            90033: (34.061, -118.208), 90034: (34.026, -118.400), 90035: (34.076, -118.361),
            90036: (34.083, -118.355), 90037: (34.007, -118.288), 90038: (34.092, -118.326),
            90039: (34.121, -118.270), 90040: (34.062, -118.206), 90041: (34.135, -118.239),
            90042: (34.114, -118.201), 90043: (33.988, -118.329), 90044: (33.955, -118.287),
            90045: (33.961, -118.378), 90046: (34.106, -118.360), 90047: (33.958, -118.308),
            90048: (34.075, -118.384), 90049: (34.046, -118.469), 90056: (33.958, -118.287),
            90057: (34.060, -118.277), 90058: (33.982, -118.235), 90059: (33.941, -118.256),
            90061: (33.984, -118.265), 90062: (33.979, -118.309), 90063: (34.036, -118.181),
            90064: (34.040, -118.428), 90065: (34.112, -118.234), 90066: (33.994, -118.427),
            90067: (34.058, -118.417), 90068: (34.118, -118.321), 90069: (34.090, -118.373),
            90077: (34.084, -118.445), 90210: (34.090, -118.406), 90211: (34.073, -118.400),
            90212: (34.066, -118.398), 90230: (33.942, -118.293), 90232: (34.086, -118.237),
            90272: (34.035, -118.476), 90291: (33.980, -118.462), 90292: (33.993, -118.472),
            90293: (33.953, -118.449), 90401: (34.017, -118.491), 90402: (34.009, -118.498),
            90403: (34.029, -118.468), 90404: (34.031, -118.458), 90405: (33.990, -118.464),
            90501: (33.888, -118.297), 90502: (33.863, -118.350), 90503: (33.888, -118.350),
            90504: (33.888, -118.327), 90505: (33.888, -118.377), 90506: (33.888, -118.403),
            90601: (33.969, -118.082), 90602: (33.955, -118.063), 90603: (33.911, -118.120),
            90604: (33.881, -118.108), 90605: (33.881, -118.069), 90606: (33.881, -118.140),
            90631: (33.918, -118.054), 90640: (33.942, -118.135), 90650: (33.920, -118.084),
            90660: (33.888, -118.062), 90670: (33.924, -118.079), 90701: (33.872, -118.238),
            90703: (33.857, -118.220), 90704: (33.805, -118.160), 90706: (33.879, -118.167),
            90712: (33.843, -118.135), 90713: (33.843, -118.108), 90715: (33.843, -118.081),
            90716: (33.809, -118.122), 90717: (33.809, -118.135), 90723: (33.809, -118.162),
            90731: (33.706, -118.291), 90732: (33.743, -118.295), 90744: (33.787, -118.275),
            90745: (33.787, -118.248), 90746: (33.787, -118.302), 90247: (33.924, -118.135),
            90248: (33.924, -118.162), 90249: (33.924, -118.189), 90250: (33.897, -118.270),
            90254: (33.897, -118.297), 90255: (33.897, -118.324), 90260: (33.897, -118.243),
            90262: (33.924, -118.243), 90270: (33.951, -118.243), 90280: (33.951, -118.270),
            90301: (33.979, -118.270), 90302: (33.979, -118.297), 90303: (33.979, -118.324),
            90304: (34.006, -118.270), 90305: (34.006, -118.297), 90501: (33.888, -118.297),
            91001: (34.162, -118.135), 91006: (34.162, -118.108), 91007: (34.189, -118.108),
            91016: (34.189, -118.135), 91024: (34.189, -118.162), 91030: (34.189, -118.189),
            91040: (34.189, -118.216), 91042: (34.216, -118.216), 91101: (34.162, -118.189),
            91103: (34.135, -118.189), 91104: (34.135, -118.162), 91105: (34.135, -118.135),
            91106: (34.108, -118.135), 91107: (34.108, -118.162), 91108: (34.108, -118.189),
            91201: (34.189, -118.243), 91202: (34.189, -118.270), 91203: (34.189, -118.297),
            91204: (34.189, -118.324), 91205: (34.189, -118.351), 91206: (34.189, -118.378),
            91207: (34.189, -118.405), 91208: (34.216, -118.243), 91210: (34.216, -118.270),
            91214: (34.216, -118.297), 91301: (34.270, -118.595), 91302: (34.270, -118.568),
            91303: (34.270, -118.541), 91304: (34.270, -118.514), 91306: (34.270, -118.487),
            91307: (34.270, -118.460), 91311: (34.270, -118.433), 91316: (34.270, -118.406),
            91320: (34.270, -118.379), 91321: (34.270, -118.352), 91324: (34.270, -118.325),
            91325: (34.270, -118.298), 91326: (34.270, -118.271), 91330: (34.270, -118.244),
            91331: (34.270, -118.217), 91335: (34.270, -118.190), 91340: (34.270, -118.163),
            91342: (34.270, -118.136), 91343: (34.270, -118.109), 91344: (34.270, -118.082),
            91345: (34.270, -118.055), 91350: (34.243, -118.595), 91351: (34.243, -118.568),
            91352: (34.243, -118.541), 91354: (34.243, -118.514), 91355: (34.243, -118.487),
            91356: (34.243, -118.460), 91361: (34.243, -118.433), 91362: (34.243, -118.406),
            91364: (34.243, -118.379), 91367: (34.243, -118.352), 91401: (34.243, -118.325),
            91402: (34.243, -118.298), 91403: (34.243, -118.271), 91405: (34.243, -118.244),
            91406: (34.243, -118.217), 91411: (34.243, -118.190), 91423: (34.243, -118.163),
            91436: (34.243, -118.136), 91501: (34.216, -118.379), 91502: (34.216, -118.352),
            91504: (34.216, -118.325), 91505: (34.216, -118.298), 91506: (34.216, -118.271),
            91601: (34.216, -118.406), 91602: (34.216, -118.433), 91604: (34.216, -118.460),
            91605: (34.216, -118.487), 91606: (34.216, -118.514), 91607: (34.216, -118.541),
        }
    
    def add_estimated_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add estimated coordinates based on ZIP codes"""
        print("Adding estimated coordinates based on ZIP codes...")
        
        # Initialize coordinate columns
        df['latitude'] = np.nan
        df['longitude'] = np.nan
        
        # Add coordinates based on ZIP codes
        for idx, row in df.iterrows():
            zip_code = row['zip_code']
            if pd.notna(zip_code) and zip_code in self.zip_coordinates:
                lat, lon = self.zip_coordinates[zip_code]
                # Add some random variation to simulate property-level precision
                lat_variation = np.random.normal(0, 0.008)  # ~0.5 mile variation
                lon_variation = np.random.normal(0, 0.008)
                
                df.at[idx, 'latitude'] = lat + lat_variation
                df.at[idx, 'longitude'] = lon + lon_variation
        
        coords_added = df[['latitude', 'longitude']].notna().all(axis=1).sum()
        print(f"✓ Added coordinates to {coords_added}/{len(df)} properties")
        
        return df
    
    def prepare_sample_data(self, csv_path: str) -> pd.DataFrame:
        """Load and prepare the sample data for scoring"""
        print(f"Loading sample data from: {csv_path}")
        
        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} properties")
        
        # Clean the data as before
        df['lot_size_sqft'] = df['lot_size'].astype(str).str.extract(r'([\d,]+\.?\d*)')[0].str.replace(',', '').astype(float)
        df['building_size_sqft'] = df['building_sqft'].astype(str).str.extract(r'([\d,]+\.?\d*)')[0].str.replace(',', '').astype(float)
        df['lot_size_sqft'] = df['lot_size_sqft'].fillna(0)
        df['building_size_sqft'] = df['building_size_sqft'].fillna(0)
        df['base_zoning'] = df['zoning'].astype(str).str.replace(r'[\[\]TQ]', '', regex=True).str.split('-').str[0]
        
        # Add coordinates
        df = self.add_estimated_coordinates(df)
        
        # Add required scoring columns
        df['toc_eligible'] = df['toc_status'].notna() & (df['toc_status'] != '')
        df['high_quality_transit'] = 'No'
        df['opportunity_zone'] = 'none'
        df['overlay_count'] = 0
        df['methane_zone'] = 'none'
        df['fault_zone'] = 'none'
        df['flood_zone'] = 'none'
        df['specific_plan_area'] = ''
        
        # Enhanced financial estimates
        df['assessed_land_value'] = df['lot_size_sqft'] * np.random.uniform(300, 1000, len(df))
        df['total_assessed_value'] = df['assessed_land_value'] + (df['building_size_sqft'] * np.random.uniform(200, 500, len(df)))
        
        df['assessor_parcel_id'] = df['apn']
        df['site_address'] = df['address']
        
        print(f"✓ Data prepared for scoring")
        return df
    
    def run_comparison_test(self, df: pd.DataFrame, sample_size: int = 200) -> Dict:
        """Run both original and enhanced scoring for comparison"""
        print(f"\nRunning comparison test on {sample_size} properties...")
        
        # Sample for faster testing
        if len(df) > sample_size:
            test_df = df.sample(sample_size, random_state=42).copy()
        else:
            test_df = df.copy()
        
        print(f"Testing on {len(test_df)} properties")
        
        # Run original scoring
        print("\n1. Running original DealGenie scoring...")
        original_results = self.original_scorer.score_properties(test_df.copy())
        
        # Run enhanced scoring with TOC
        print("\n2. Running TOC-enhanced scoring...")
        enhanced_df = self.enhanced_scorer.add_toc_data_to_properties(test_df.copy())
        enhanced_results = self.enhanced_scorer.score_properties(enhanced_df)
        
        return {
            'original': original_results,
            'enhanced': enhanced_results,
            'test_size': len(test_df)
        }
    
    def analyze_score_improvements(self, results: Dict) -> Dict:
        """Analyze the improvements from TOC integration"""
        original = results['original']
        enhanced = results['enhanced']
        
        # Score comparison
        original_scores = original['development_score']
        enhanced_scores = enhanced['development_score']
        
        # Investment grade analysis
        original_investment_grade = (original_scores >= 70).sum()
        enhanced_investment_grade = (enhanced_scores >= 70).sum()
        
        # Score improvements
        score_improvements = enhanced_scores - original_scores
        
        # Tier changes
        original_tiers = original['investment_tier'].value_counts()
        enhanced_tiers = enhanced['investment_tier'].value_counts()
        
        analysis = {
            'score_changes': {
                'original_mean': original_scores.mean(),
                'enhanced_mean': enhanced_scores.mean(),
                'mean_improvement': score_improvements.mean(),
                'max_improvement': score_improvements.max(),
                'properties_improved': (score_improvements > 0).sum(),
                'properties_with_toc': (enhanced['toc_toc_tier'] > 0).sum()
            },
            'investment_grade': {
                'original_count': original_investment_grade,
                'enhanced_count': enhanced_investment_grade,
                'new_investment_grade': enhanced_investment_grade - original_investment_grade
            },
            'tier_distribution': {
                'original': original_tiers.to_dict(),
                'enhanced': enhanced_tiers.to_dict()
            },
            'top_improvements': enhanced.nlargest(10, 'development_score')[
                ['apn', 'address', 'base_zoning', 'lot_size_sqft', 'toc_toc_tier', 
                 'toc_nearest_station', 'development_score', 'investment_tier', 'suggested_use']
            ].to_dict('records')
        }
        
        return analysis
    
    def generate_validation_report(self, results: Dict, analysis: Dict):
        """Generate comprehensive validation report"""
        print(f"\n" + "="*80)
        print("TOC INTEGRATION VALIDATION REPORT")
        print("="*80)
        
        # Overall improvements
        score_changes = analysis['score_changes']
        investment_changes = analysis['investment_grade']
        
        print(f"\n📊 SCORE IMPROVEMENTS")
        print(f"   • Original average score: {score_changes['original_mean']:.1f}")
        print(f"   • Enhanced average score: {score_changes['enhanced_mean']:.1f}")
        print(f"   • Average improvement: +{score_changes['mean_improvement']:.1f} points")
        print(f"   • Maximum improvement: +{score_changes['max_improvement']:.1f} points")
        print(f"   • Properties improved: {score_changes['properties_improved']}/{results['test_size']}")
        print(f"   • Properties with TOC bonus: {score_changes['properties_with_toc']}")
        
        print(f"\n🎯 INVESTMENT GRADE ANALYSIS")
        print(f"   • Original investment grade (70+): {investment_changes['original_count']}")
        print(f"   • Enhanced investment grade (70+): {investment_changes['enhanced_count']}")
        print(f"   • NEW investment opportunities: +{investment_changes['new_investment_grade']}")
        
        if investment_changes['enhanced_count'] > 0:
            success_rate = investment_changes['enhanced_count'] / results['test_size'] * 100
            print(f"   • Investment grade success rate: {success_rate:.1f}%")
        
        # Tier distribution changes
        print(f"\n📈 TIER DISTRIBUTION CHANGES")
        original_tiers = analysis['tier_distribution']['original']
        enhanced_tiers = analysis['tier_distribution']['enhanced']
        
        all_tiers = set(list(original_tiers.keys()) + list(enhanced_tiers.keys()))
        for tier in sorted(all_tiers):
            orig_count = original_tiers.get(tier, 0)
            enh_count = enhanced_tiers.get(tier, 0)
            change = enh_count - orig_count
            change_str = f"+{change}" if change > 0 else str(change) if change < 0 else "0"
            print(f"   • Tier {tier}: {orig_count} → {enh_count} ({change_str})")
        
        # Top performing properties
        print(f"\n🏆 TOP 10 ENHANCED PROPERTIES")
        print("-" * 80)
        for i, prop in enumerate(analysis['top_improvements'], 1):
            print(f"{i:2d}. Score: {prop['development_score']:.1f} | Tier: {prop['investment_tier']} | TOC Tier: {prop['toc_toc_tier']}")
            print(f"    {prop['address']}")
            print(f"    {prop['base_zoning']} | {prop['lot_size_sqft']:,.0f} sqft | Near: {prop['toc_nearest_station']}")
            print(f"    Use: {prop['suggested_use']}")
            print()
        
        # Success assessment
        print(f"✅ TOC INTEGRATION SUCCESS ASSESSMENT")
        if investment_changes['enhanced_count'] >= 10:
            status = "EXCELLENT - Strong investment pipeline created"
        elif investment_changes['enhanced_count'] >= 5:
            status = "GOOD - Meaningful investment opportunities identified"
        elif investment_changes['enhanced_count'] >= 1:
            status = "MODERATE - Some investment opportunities created"
        else:
            status = "NEEDS FURTHER CALIBRATION - No investment grade properties"
        
        print(f"   Status: {status}")
        print(f"   Ready for production: {'YES' if investment_changes['enhanced_count'] >= 5 else 'NEEDS MORE CALIBRATION'}")
        
        return status
    
    def export_results(self, results: Dict, analysis: Dict):
        """Export results to CSV files"""
        print(f"\nExporting results...")
        
        # Export enhanced results
        enhanced_file = "dealgenie_v4_3_toc_enhanced_results.csv"
        results['enhanced'].to_csv(enhanced_file, index=False)
        print(f"✓ Enhanced results: {enhanced_file}")
        
        # Export comparison
        comparison_df = pd.DataFrame({
            'apn': results['original']['apn'],
            'address': results['original']['address'],
            'base_zoning': results['original']['base_zoning'],
            'lot_size_sqft': results['original']['lot_size_sqft'],
            'original_score': results['original']['development_score'],
            'enhanced_score': results['enhanced']['development_score'],
            'score_improvement': results['enhanced']['development_score'] - results['original']['development_score'],
            'original_tier': results['original']['investment_tier'],
            'enhanced_tier': results['enhanced']['investment_tier'],
            'toc_tier': results['enhanced']['toc_toc_tier'],
            'toc_station': results['enhanced']['toc_nearest_station'],
            'enhanced_use_case': results['enhanced']['suggested_use']
        })
        
        comparison_file = "dealgenie_toc_comparison_results.csv"
        comparison_df.to_csv(comparison_file, index=False)
        print(f"✓ Comparison results: {comparison_file}")
        
        # Export analysis summary
        analysis_file = "dealgenie_toc_analysis_summary.json"
        with open(analysis_file, 'w') as f:
            # Convert non-serializable objects
            export_analysis = analysis.copy()
            export_analysis['top_improvements'] = analysis['top_improvements']  # Already serializable
            json.dump(export_analysis, f, indent=2, default=str)
        print(f"✓ Analysis summary: {analysis_file}")
    
    def run_full_test(self, csv_path: str, sample_size: int = 200):
        """Run the complete TOC enhancement test"""
        print("="*80)
        print("DEALGENIE V4.3 TOC INTEGRATION TEST")
        print("="*80)
        
        # Prepare data
        df = self.prepare_sample_data(csv_path)
        
        # Run comparison
        results = self.run_comparison_test(df, sample_size)
        
        # Analyze improvements
        analysis = self.analyze_score_improvements(results)
        
        # Generate report
        status = self.generate_validation_report(results, analysis)
        
        # Export results
        self.export_results(results, analysis)
        
        return {
            'results': results,
            'analysis': analysis,
            'status': status
        }


def main():
    """Main test execution"""
    test_runner = TOCTestRunner()
    
    # Run test on sample
    csv_path = "/Users/samanthagrant/Desktop/dealgenie/scraper/diverse_dealgenie_sample_1000.csv"
    final_results = test_runner.run_full_test(csv_path, sample_size=300)
    
    print(f"\n🎉 TOC integration testing complete!")
    print(f"Status: {final_results['status']}")


if __name__ == "__main__":
    main()