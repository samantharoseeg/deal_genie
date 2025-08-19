#!/usr/bin/env python3
"""
DealGenie V4.3 Calibration Analysis & Enhanced Testing
======================================================

Analyze calibration issues and test with optimized property samples
to validate scoring accuracy and identify improvement opportunities.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from dealgenie_scoring_engine import DealGenieScorer


class DealGenieCalibrationAnalyzer:
    """Analyze and improve DealGenie scoring calibration"""
    
    def __init__(self):
        self.scorer = DealGenieScorer()
        
    def load_full_dataset(self, csv_path: str) -> pd.DataFrame:
        """Load and prepare the full diverse dataset"""
        print("Loading full diverse ZIMAS dataset...")
        df = pd.read_csv(csv_path)
        
        # Clean the data as before
        df['lot_size_sqft'] = df['lot_size'].astype(str).str.extract(r'([\d,]+\.?\d*)')[0].str.replace(',', '').astype(float)
        df['building_size_sqft'] = df['building_sqft'].astype(str).str.extract(r'([\d,]+\.?\d*)')[0].str.replace(',', '').astype(float)
        df['lot_size_sqft'] = df['lot_size_sqft'].fillna(0)
        df['building_size_sqft'] = df['building_size_sqft'].fillna(0)
        df['base_zoning'] = df['zoning'].astype(str).str.replace(r'[\[\]TQ]', '', regex=True).str.split('-').str[0]
        
        # Add scoring columns
        df['toc_eligible'] = df['toc_status'].notna() & (df['toc_status'] != '')
        df['high_quality_transit'] = 'No'
        df['opportunity_zone'] = 'none'
        df['overlay_count'] = 0
        df['methane_zone'] = 'none'
        df['fault_zone'] = 'none'
        df['flood_zone'] = 'none'
        df['specific_plan_area'] = ''
        
        # Financial estimates
        df['assessed_land_value'] = df['lot_size_sqft'] * np.random.uniform(200, 800, len(df))
        df['total_assessed_value'] = df['assessed_land_value'] + (df['building_size_sqft'] * np.random.uniform(150, 400, len(df)))
        
        df['assessor_parcel_id'] = df['apn']
        df['site_address'] = df['address']
        
        print(f"✓ Loaded and cleaned {len(df)} properties")
        return df
    
    def identify_calibration_issues(self, df: pd.DataFrame):
        """Identify specific calibration issues in the scoring system"""
        print("\nCALIBRATION ISSUE ANALYSIS")
        print("="*50)
        
        # Test a small sample first
        test_sample = df.sample(min(100, len(df)), random_state=42)
        scored_sample = self.scorer.score_properties(test_sample.copy())
        
        issues = []
        
        # Issue 1: All properties scoring too low
        max_score = scored_sample['development_score'].max()
        mean_score = scored_sample['development_score'].mean()
        print(f"Score Analysis:")
        print(f"  Maximum score in sample: {max_score:.1f}")
        print(f"  Average score: {mean_score:.1f}")
        
        if max_score < 70:
            issues.append("ISSUE: Maximum scores are too low - no properties reach investment grade")
        
        if mean_score < 45:
            issues.append("ISSUE: Average scores are too conservative")
        
        # Issue 2: Transit bonus not being applied
        transit_bonus_count = scored_sample.apply(
            lambda row: json.loads(row['score_breakdown'])['transit_bonus'] > 0, axis=1
        ).sum()
        print(f"  Properties with transit bonus: {transit_bonus_count}")
        
        if transit_bonus_count == 0:
            issues.append("ISSUE: Transit bonuses are not being applied (missing TOC/transit data)")
        
        # Issue 3: High-density zoning not getting appropriate scores
        high_density = scored_sample[scored_sample['base_zoning'].isin(['R3', 'R4', 'R5', 'C2', 'C4'])]
        if len(high_density) > 0:
            high_density_avg = high_density['development_score'].mean()
            print(f"  High-density zoning average score: {high_density_avg:.1f}")
            
            if high_density_avg < 60:
                issues.append("ISSUE: High-density zones scoring too low")
        
        # Issue 4: Large lots not getting assembly bonuses
        large_lots = scored_sample[scored_sample['lot_size_sqft'] > 15000]
        if len(large_lots) > 0:
            large_lot_avg = large_lots['development_score'].mean()
            print(f"  Large lots (>15k sqft) average score: {large_lot_avg:.1f}")
            
            if large_lot_avg < 65:
                issues.append("ISSUE: Large lots not receiving appropriate assembly bonuses")
        
        print(f"\nIdentified Issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        return issues, scored_sample
    
    def create_optimized_test_properties(self) -> pd.DataFrame:
        """Create optimized property scenarios for testing high scores"""
        print(f"\nCreating optimized test properties...")
        
        properties = []
        
        # 1. Premium TOC Multi-Family Development
        properties.append({
            'apn': 'TEST_001',
            'address': 'TEST - Premium TOC Site',
            'zip_code': 90028,
            'base_zoning': 'R4',
            'lot_size_sqft': 25000,
            'building_size_sqft': 2000,  # Low FAR for redevelopment
            'units': 2,
            'toc_eligible': True,
            'high_quality_transit': 'Yes',
            'opportunity_zone': 'tier 1',
            'overlay_count': 0,
            'methane_zone': 'none',
            'fault_zone': 'none',
            'flood_zone': 'none',
            'specific_plan_area': '',
            'assessed_land_value': 15000000,  # High land value
            'total_assessed_value': 15500000,  # High land ratio
            'assessor_parcel_id': 'TEST_001',
            'site_address': 'TEST - Premium TOC Site'
        })
        
        # 2. Large Commercial Assembly
        properties.append({
            'apn': 'TEST_002',
            'address': 'TEST - Commercial Assembly',
            'zip_code': 90028,
            'base_zoning': 'C4',
            'lot_size_sqft': 50000,
            'building_size_sqft': 5000,
            'units': 1,
            'toc_eligible': True,
            'high_quality_transit': 'Yes',
            'opportunity_zone': 'tier 2',
            'overlay_count': 0,
            'methane_zone': 'none',
            'fault_zone': 'none',
            'flood_zone': 'none',
            'specific_plan_area': '',
            'assessed_land_value': 25000000,
            'total_assessed_value': 27000000,
            'assessor_parcel_id': 'TEST_002',
            'site_address': 'TEST - Commercial Assembly'
        })
        
        # 3. High-Density Transit Hub
        properties.append({
            'apn': 'TEST_003',
            'address': 'TEST - Transit Hub Development',
            'zip_code': 90013,
            'base_zoning': 'R5',
            'lot_size_sqft': 35000,
            'building_size_sqft': 3000,
            'units': 4,
            'toc_eligible': True,
            'high_quality_transit': 'Yes',
            'opportunity_zone': 'tier 1',
            'overlay_count': 0,
            'methane_zone': 'none',
            'fault_zone': 'none',
            'flood_zone': 'none',
            'specific_plan_area': '',
            'assessed_land_value': 20000000,
            'total_assessed_value': 21000000,
            'assessor_parcel_id': 'TEST_003',
            'site_address': 'TEST - Transit Hub Development'
        })
        
        # 4. Mixed-Use Opportunity
        properties.append({
            'apn': 'TEST_004',
            'address': 'TEST - Mixed Use Development',
            'zip_code': 90028,
            'base_zoning': 'CM',
            'lot_size_sqft': 15000,
            'building_size_sqft': 1500,
            'units': 1,
            'toc_eligible': True,
            'high_quality_transit': 'Yes',
            'opportunity_zone': 'oc-2',
            'overlay_count': 0,
            'methane_zone': 'none',
            'fault_zone': 'none',
            'flood_zone': 'none',
            'specific_plan_area': '',
            'assessed_land_value': 8000000,
            'total_assessed_value': 8500000,
            'assessor_parcel_id': 'TEST_004',
            'site_address': 'TEST - Mixed Use Development'
        })
        
        # 5. Industrial Creative Office
        properties.append({
            'apn': 'TEST_005',
            'address': 'TEST - Creative Office Conversion',
            'zip_code': 90021,
            'base_zoning': 'M1',
            'lot_size_sqft': 20000,
            'building_size_sqft': 8000,
            'units': 1,
            'toc_eligible': False,
            'high_quality_transit': 'No',
            'opportunity_zone': 'tier 3',
            'overlay_count': 0,
            'methane_zone': 'none',
            'fault_zone': 'none',
            'flood_zone': 'none',
            'specific_plan_area': '',
            'assessed_land_value': 12000000,
            'total_assessed_value': 15000000,
            'assessor_parcel_id': 'TEST_005',
            'site_address': 'TEST - Creative Office Conversion'
        })
        
        df = pd.DataFrame(properties)
        print(f"✓ Created {len(df)} optimized test properties")
        return df
    
    def test_optimized_properties(self, optimized_df: pd.DataFrame):
        """Test the optimized properties to see maximum potential scores"""
        print(f"\nTesting optimized properties...")
        
        scored_df = self.scorer.score_properties(optimized_df.copy())
        
        print(f"\nOPTIMIZED PROPERTY RESULTS:")
        print("="*60)
        
        for idx, row in scored_df.iterrows():
            score_breakdown = json.loads(row['score_breakdown'])
            
            print(f"\n{row['site_address']}")
            print(f"Zoning: {row['base_zoning']} | Lot: {row['lot_size_sqft']:,} sqft")
            print(f"Score: {row['development_score']:.1f} | Tier: {row['investment_tier']}")
            print(f"Use Case: {row['suggested_use']}")
            print("Component Breakdown:")
            for component, score in score_breakdown.items():
                print(f"  {component}: {score:.1f}")
            print("-" * 40)
        
        return scored_df
    
    def find_best_real_properties(self, df: pd.DataFrame, n_properties: int = 10):
        """Find the best-scoring real properties from the dataset"""
        print(f"\nIdentifying top real properties...")
        
        # Pre-filter for promising properties
        promising = df[
            (df['lot_size_sqft'] >= 5000) |  # Large enough lots
            (df['base_zoning'].isin(['R3', 'R4', 'R5', 'C2', 'C4', 'CM'])) |  # High-value zoning
            (df['units'] > 2)  # Multi-family existing
        ].copy()
        
        print(f"Pre-filtered to {len(promising)} promising properties")
        
        if len(promising) > 500:
            # Sample if too many
            test_sample = promising.sample(500, random_state=42)
        else:
            test_sample = promising.copy()
        
        # Score the promising properties
        scored_sample = self.scorer.score_properties(test_sample)
        
        # Get top performers
        top_properties = scored_sample.nlargest(n_properties, 'development_score')
        
        print(f"\nTOP {n_properties} REAL PROPERTIES:")
        print("="*60)
        
        for idx, row in top_properties.iterrows():
            score_breakdown = json.loads(row['score_breakdown'])
            
            print(f"\nAPN: {row['apn']}")
            print(f"Address: {row['address']}")
            print(f"Zoning: {row['base_zoning']} | Lot: {row['lot_size_sqft']:,.0f} sqft | Units: {row['units']}")
            print(f"Score: {row['development_score']:.1f} | Tier: {row['investment_tier']}")
            print(f"Use Case: {row['suggested_use']}")
            print("Components:")
            for component, score in score_breakdown.items():
                print(f"  {component}: {score:.1f}")
            print("-" * 40)
        
        return top_properties
    
    def suggest_calibration_improvements(self, issues: List[str], real_top: pd.DataFrame, optimized_results: pd.DataFrame):
        """Suggest specific calibration improvements"""
        print(f"\nCALIBRATION IMPROVEMENT RECOMMENDATIONS")
        print("="*60)
        
        recommendations = []
        
        # Check if transit bonuses are working
        max_optimized_score = optimized_results['development_score'].max()
        max_real_score = real_top['development_score'].max()
        
        print(f"Score Analysis:")
        print(f"  Maximum optimized property score: {max_optimized_score:.1f}")
        print(f"  Maximum real property score: {max_real_score:.1f}")
        
        if max_optimized_score < 80:
            recommendations.append({
                'issue': 'Transit bonus weighting too low',
                'solution': 'Increase transit_bonus weight from 0.20 to 0.30',
                'impact': 'Would boost high-quality transit properties by ~10 points'
            })
        
        if max_real_score < 60:
            recommendations.append({
                'issue': 'Real properties scoring too conservatively',
                'solution': 'Adjust lot_size_score thresholds or increase zoning scores for R3/R4/R5',
                'impact': 'Would improve scores for development-ready properties'
            })
        
        # Check zoning score distribution
        zoning_performance = {}
        for df_name, df in [('Real', real_top), ('Optimized', optimized_results)]:
            zoning_avg = df.groupby('base_zoning')['development_score'].mean()
            zoning_performance[df_name] = zoning_avg
        
        print(f"\nZoning Performance Comparison:")
        for zoning in ['R3', 'R4', 'R5', 'C2', 'C4']:
            real_score = zoning_performance['Real'].get(zoning, 0)
            opt_score = zoning_performance['Optimized'].get(zoning, 0)
            print(f"  {zoning}: Real={real_score:.1f}, Optimized={opt_score:.1f}")
            
            if zoning in ['R4', 'R5'] and opt_score < 75:
                recommendations.append({
                    'issue': f'{zoning} zoning scoring too low',
                    'solution': f'Increase {zoning} base score from current to 95+',
                    'impact': f'Would properly reward high-density development potential'
                })
        
        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. ISSUE: {rec['issue']}")
            print(f"   SOLUTION: {rec['solution']}")
            print(f"   IMPACT: {rec['impact']}")
        
        return recommendations
    
    def run_comprehensive_calibration_analysis(self, csv_path: str):
        """Run complete calibration analysis"""
        print("="*80)
        print("DEALGENIE V4.3 CALIBRATION ANALYSIS")
        print("="*80)
        
        # 1. Load full dataset
        df = self.load_full_dataset(csv_path)
        
        # 2. Identify calibration issues
        issues, sample_scored = self.identify_calibration_issues(df)
        
        # 3. Test optimized properties
        optimized_df = self.create_optimized_test_properties()
        optimized_results = self.test_optimized_properties(optimized_df)
        
        # 4. Find best real properties
        real_top = self.find_best_real_properties(df, 10)
        
        # 5. Generate recommendations
        recommendations = self.suggest_calibration_improvements(issues, real_top, optimized_results)
        
        # 6. Final assessment
        print(f"\n" + "="*80)
        print("FINAL CALIBRATION ASSESSMENT")
        print("="*80)
        
        optimized_avg = optimized_results['development_score'].mean()
        real_avg = real_top['development_score'].mean()
        
        print(f"📊 SCORE SUMMARY:")
        print(f"   • Best optimized properties average: {optimized_avg:.1f}")
        print(f"   • Best real properties average: {real_avg:.1f}")
        print(f"   • Score gap: {optimized_avg - real_avg:.1f} points")
        
        print(f"\n🎯 CALIBRATION STATUS:")
        if optimized_avg >= 75 and real_avg >= 55:
            status = "WELL CALIBRATED - Minor adjustments needed"
        elif optimized_avg >= 70:
            status = "MODERATE CALIBRATION - Transit bonuses working but conservative"
        else:
            status = "NEEDS RECALIBRATION - Scores too conservative across the board"
        
        print(f"   {status}")
        
        print(f"\n🏗️ PRODUCTION RECOMMENDATIONS:")
        print(f"   • {len(recommendations)} calibration improvements identified")
        print(f"   • Focus on transit bonus integration and zoning score adjustments")
        print(f"   • Test with actual TOC/transit data for better accuracy")
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'optimized_results': optimized_results,
            'real_top_properties': real_top,
            'calibration_status': status
        }


def main():
    """Main analysis execution"""
    analyzer = DealGenieCalibrationAnalyzer()
    
    csv_path = "/Users/samanthagrant/Desktop/dealgenie/scraper/diverse_dealgenie_sample_1000.csv"
    results = analyzer.run_comprehensive_calibration_analysis(csv_path)
    
    # Save results
    output_file = "dealgenie_calibration_analysis_2025-08-19.json"
    
    # Prepare results for JSON (convert DataFrames)
    json_results = {
        'issues': results['issues'],
        'recommendations': results['recommendations'],
        'calibration_status': results['calibration_status'],
        'optimized_property_count': len(results['optimized_results']),
        'real_property_count': len(results['real_top_properties'])
    }
    
    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 Calibration analysis saved to: {output_file}")


if __name__ == "__main__":
    main()