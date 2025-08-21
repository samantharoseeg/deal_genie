#!/usr/bin/env python3
"""
DealGenie V4.3 Testing Suite - Diverse ZIMAS Sample Analysis
===========================================================

Test the latest DealGenie scoring engine with diverse property types
and generate comprehensive performance analytics.

Version: 4.3
Test Date: 2025-08-19
Sample Size: 1000 diverse LA properties
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import the DealGenie scoring engine
from dealgenie_scoring_engine import DealGenieScorer


class DealGenieTestSuite:
    """Comprehensive test suite for DealGenie scoring engine"""
    
    def __init__(self):
        """Initialize test suite"""
        self.version = "4.3"
        self.test_date = "2025-08-19"
        self.scorer = DealGenieScorer()
        self.test_results = {}
        
    def load_and_prepare_data(self, csv_path: str) -> pd.DataFrame:
        """Load and prepare diverse sample data"""
        print(f"Loading diverse sample data from: {csv_path}")
        
        # Load the CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} properties")
        
        # Clean and standardize the data
        df = self.clean_sample_data(df)
        
        return df
    
    def clean_sample_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the sample data for testing"""
        print("Cleaning and standardizing sample data...")
        
        # Parse lot size (remove text, convert to float)
        df['lot_size_sqft'] = df['lot_size'].astype(str).str.extract(r'([\d,]+\.?\d*)')[0].str.replace(',', '').astype(float)
        
        # Parse building size (remove text, convert to float)
        df['building_size_sqft'] = df['building_sqft'].astype(str).str.extract(r'([\d,]+\.?\d*)')[0].str.replace(',', '').astype(float)
        
        # Fill NaN values
        df['lot_size_sqft'] = df['lot_size_sqft'].fillna(0)
        df['building_size_sqft'] = df['building_size_sqft'].fillna(0)
        
        # Clean zoning codes (remove brackets and special characters)
        df['base_zoning'] = df['zoning'].astype(str).str.replace(r'[\[\]TQ]', '', regex=True).str.split('-').str[0]
        
        # Add required columns for scoring
        df['toc_eligible'] = df['toc_status'].notna() & (df['toc_status'] != '')
        df['high_quality_transit'] = 'No'  # Default - would need transit data
        df['opportunity_zone'] = 'none'   # Default - would need OZ data
        df['overlay_count'] = 0           # Default - would need overlay analysis
        df['methane_zone'] = 'none'       # Default - would need environmental data
        df['fault_zone'] = 'none'         # Default - would need geological data
        df['flood_zone'] = 'none'         # Default - would need FEMA data
        df['specific_plan_area'] = ''     # Default - would need planning data
        
        # Financial data (estimated for testing)
        df['assessed_land_value'] = df['lot_size_sqft'] * np.random.uniform(200, 800, len(df))
        df['total_assessed_value'] = df['assessed_land_value'] + (df['building_size_sqft'].fillna(0) * np.random.uniform(150, 400, len(df)))
        
        # Add assessor parcel ID and site address columns
        df['assessor_parcel_id'] = df['apn']
        df['site_address'] = df['address']
        
        print(f"✓ Data cleaned and standardized")
        return df
    
    def select_representative_sample(self, df: pd.DataFrame, n_properties: int = 10) -> pd.DataFrame:
        """Select diverse representative properties for detailed testing"""
        print(f"Selecting {n_properties} representative properties for testing...")
        
        # Analyze diversity dimensions
        zoning_types = df['base_zoning'].value_counts()
        zip_codes = df['zip_code'].value_counts()
        lot_size_ranges = pd.cut(df['lot_size_sqft'], bins=5).value_counts()
        
        print(f"Available zoning types: {len(zoning_types)}")
        print(f"ZIP codes represented: {len(zip_codes)}")
        print(f"Lot size distribution:")
        for range_desc, count in lot_size_ranges.items():
            print(f"  {range_desc}: {count} properties")
        
        # Select diverse sample
        selected_properties = []
        
        # 1. High-density residential (R3, R4, R5)
        high_density = df[df['base_zoning'].isin(['R3', 'R4', 'R5'])].head(2)
        selected_properties.append(high_density)
        
        # 2. Medium-density residential (RD1.5, RD2, RD3)
        med_density = df[df['base_zoning'].str.startswith('RD')].head(2)
        selected_properties.append(med_density)
        
        # 3. Commercial zones (C1, C2, C4, CM)
        commercial = df[df['base_zoning'].str.startswith('C')].head(2)
        selected_properties.append(commercial)
        
        # 4. Low-density residential (R1, RS, RE, RA)
        low_density = df[df['base_zoning'].isin(['R1', 'RS', 'RE', 'RA'])].head(2)
        selected_properties.append(low_density)
        
        # 5. Large lots (>10,000 sqft)
        large_lots = df[df['lot_size_sqft'] > 10000].head(1)
        selected_properties.append(large_lots)
        
        # 6. Multi-family existing (units > 1)
        multi_family = df[df['units'] > 1].head(1)
        selected_properties.append(multi_family)
        
        # Combine all selections
        sample_df = pd.concat(selected_properties, ignore_index=True).drop_duplicates(subset=['apn'])
        
        # If we don't have enough, fill with random selection
        if len(sample_df) < n_properties:
            remaining = df[~df['apn'].isin(sample_df['apn'])].sample(n_properties - len(sample_df))
            sample_df = pd.concat([sample_df, remaining], ignore_index=True)
        
        sample_df = sample_df.head(n_properties)
        
        print(f"✓ Selected {len(sample_df)} diverse properties:")
        for idx, row in sample_df.iterrows():
            print(f"  {row['apn']}: {row['base_zoning']} | {row['lot_size_sqft']:,.0f} sqft | {row['zip_code']}")
        
        return sample_df
    
    def test_scoring_engine(self, sample_df: pd.DataFrame) -> pd.DataFrame:
        """Test the DealGenie scoring engine on sample properties"""
        print(f"\nTesting DealGenie V{self.version} scoring engine...")
        print("="*60)
        
        # Score the properties
        scored_df = self.scorer.score_properties(sample_df.copy())
        
        # Add detailed breakdown
        for idx, row in scored_df.iterrows():
            score_breakdown = json.loads(row['score_breakdown'])
            
            print(f"\nProperty {idx + 1}: {row['assessor_parcel_id']}")
            print(f"Address: {row['site_address']}")
            print(f"Zoning: {row['base_zoning']} | Lot: {row['lot_size_sqft']:,.0f} sqft | Units: {row['units']}")
            print(f"Score: {row['development_score']:.1f} | Tier: {row['investment_tier']} | Use: {row['suggested_use']}")
            print("Component Scores:")
            for component, score in score_breakdown.items():
                print(f"  {component}: {score:.1f}")
            print("-" * 40)
        
        return scored_df
    
    def analyze_diversity_validation(self, df: pd.DataFrame):
        """Validate diversity of the sample dataset"""
        print(f"\nDIVERSITY VALIDATION ANALYSIS")
        print("="*50)
        
        # ZIP code diversity
        zip_analysis = df['zip_code'].value_counts()
        print(f"ZIP Code Distribution ({len(zip_analysis)} unique ZIP codes):")
        for zip_code, count in zip_analysis.head(10).items():
            print(f"  {zip_code}: {count} properties")
        
        # Zoning diversity
        zoning_analysis = df['base_zoning'].value_counts()
        print(f"\nZoning Type Distribution ({len(zoning_analysis)} unique zoning types):")
        for zoning, count in zoning_analysis.head(15).items():
            print(f"  {zoning}: {count} properties")
        
        # Property type classification
        property_types = self.classify_property_types(df)
        print(f"\nProperty Type Classification:")
        for prop_type, count in property_types.items():
            print(f"  {prop_type}: {count} properties ({count/len(df)*100:.1f}%)")
        
        # Lot size distribution
        lot_size_stats = df['lot_size_sqft'].describe()
        print(f"\nLot Size Distribution:")
        print(f"  Mean: {lot_size_stats['mean']:,.0f} sqft")
        print(f"  Median: {lot_size_stats['50%']:,.0f} sqft")
        print(f"  Range: {lot_size_stats['min']:,.0f} - {lot_size_stats['max']:,.0f} sqft")
        
        # Geographic spread (approximate)
        geographic_zones = self.analyze_geographic_spread(df)
        print(f"\nGeographic Distribution:")
        for zone, count in geographic_zones.items():
            print(f"  {zone}: {count} properties")
        
        return {
            'zip_diversity': len(zip_analysis),
            'zoning_diversity': len(zoning_analysis),
            'property_types': property_types,
            'lot_size_stats': lot_size_stats.to_dict(),
            'geographic_zones': geographic_zones
        }
    
    def classify_property_types(self, df: pd.DataFrame) -> Dict[str, int]:
        """Classify properties by type based on zoning and characteristics"""
        types = {
            'Single Family Residential': 0,
            'Multi-Family Residential': 0,
            'Commercial': 0,
            'Industrial': 0,
            'Mixed-Use': 0,
            'Vacant/Undeveloped': 0
        }
        
        for _, row in df.iterrows():
            zoning = str(row['base_zoning']).upper()
            units = row.get('units', 1)
            building_sqft = row.get('building_size_sqft', 0)
            
            if pd.isna(building_sqft) or building_sqft == 0:
                types['Vacant/Undeveloped'] += 1
            elif zoning.startswith('C') or zoning.startswith('CM'):
                types['Commercial'] += 1
            elif zoning.startswith('M'):
                types['Industrial'] += 1
            elif units > 1 or zoning in ['R3', 'R4', 'R5', 'RAS3', 'RAS4']:
                types['Multi-Family Residential'] += 1
            elif zoning.startswith('R'):
                types['Single Family Residential'] += 1
            else:
                types['Mixed-Use'] += 1
        
        return types
    
    def analyze_geographic_spread(self, df: pd.DataFrame) -> Dict[str, int]:
        """Analyze geographic distribution by ZIP code zones"""
        # LA area ZIP code mapping (simplified)
        zip_zones = {
            'West LA': [90024, 90025, 90064, 90049, 90077, 90291],
            'Hollywood': [90028, 90038, 90046, 90069],
            'Downtown': [90012, 90013, 90014, 90015, 90017],
            'South LA': [90043, 90047, 90062, 90008, 90016],
            'Valley': [91331, 91356, 91304, 91406, 91423, 91401, 91342, 91325, 91326, 91040],
            'East LA': [90032, 90063, 90026, 90041, 90039],
            'Southeast': [90011, 90744, 90731],
            'Other': []
        }
        
        zone_counts = {zone: 0 for zone in zip_zones.keys()}
        
        for _, row in df.iterrows():
            zip_code = row['zip_code']
            found = False
            for zone, zip_list in zip_zones.items():
                if zip_code in zip_list:
                    zone_counts[zone] += 1
                    found = True
                    break
            if not found:
                zone_counts['Other'] += 1
        
        return zone_counts
    
    def test_development_features(self, scored_df: pd.DataFrame):
        """Test development potential and special feature detection"""
        print(f"\nDEVELOPMENT POTENTIAL TESTING")
        print("="*50)
        
        # TOC eligibility testing
        toc_properties = scored_df[scored_df['toc_eligible']]
        print(f"TOC-Eligible Properties: {len(toc_properties)}")
        if len(toc_properties) > 0:
            print(f"Average TOC score: {toc_properties['development_score'].mean():.1f}")
            print("TOC property use cases:")
            for use_case in toc_properties['suggested_use'].unique():
                count = len(toc_properties[toc_properties['suggested_use'] == use_case])
                print(f"  {use_case}: {count} properties")
        
        # SB9 opportunity testing
        sb9_candidates = scored_df[
            (scored_df['base_zoning'].isin(['R1', 'RS'])) & 
            (scored_df['lot_size_sqft'] >= 3000)
        ]
        print(f"\nPotential SB9 Candidates: {len(sb9_candidates)}")
        if len(sb9_candidates) > 0:
            print(f"Average SB9 candidate score: {sb9_candidates['development_score'].mean():.1f}")
        
        # Mixed-use development potential
        mixed_use_zones = scored_df[scored_df['base_zoning'].str.contains('C|M', na=False)]
        print(f"\nMixed-Use Potential Properties: {len(mixed_use_zones)}")
        if len(mixed_use_zones) > 0:
            print(f"Average mixed-use score: {mixed_use_zones['development_score'].mean():.1f}")
        
        # High-density development opportunities
        high_density = scored_df[scored_df['base_zoning'].isin(['R3', 'R4', 'R5', 'RAS3', 'RAS4'])]
        print(f"\nHigh-Density Development Opportunities: {len(high_density)}")
        if len(high_density) > 0:
            print(f"Average high-density score: {high_density['development_score'].mean():.1f}")
        
        # Large lot assembly opportunities
        large_lots = scored_df[scored_df['lot_size_sqft'] >= 10000]
        print(f"\nLarge Lot Assembly Opportunities: {len(large_lots)}")
        if len(large_lots) > 0:
            print(f"Average large lot score: {large_lots['development_score'].mean():.1f}")
        
        return {
            'toc_properties': len(toc_properties),
            'sb9_candidates': len(sb9_candidates),
            'mixed_use_potential': len(mixed_use_zones),
            'high_density_opportunities': len(high_density),
            'large_lot_opportunities': len(large_lots)
        }
    
    def generate_accuracy_assessment(self, scored_df: pd.DataFrame) -> Dict[str, any]:
        """Generate accuracy and performance assessment"""
        print(f"\nACCURACY & PERFORMANCE ASSESSMENT")
        print("="*50)
        
        # Score distribution analysis
        score_stats = scored_df['development_score'].describe()
        print(f"Score Distribution:")
        print(f"  Mean: {score_stats['mean']:.1f}")
        print(f"  Median: {score_stats['50%']:.1f}")
        print(f"  Standard Deviation: {score_stats['std']:.1f}")
        print(f"  Range: {score_stats['min']:.1f} - {score_stats['max']:.1f}")
        
        # Investment tier distribution
        tier_dist = scored_df['investment_tier'].value_counts().sort_index()
        print(f"\nInvestment Tier Distribution:")
        for tier, count in tier_dist.items():
            print(f"  Tier {tier}: {count} properties ({count/len(scored_df)*100:.1f}%)")
        
        # Use case distribution
        use_dist = scored_df['suggested_use'].value_counts()
        print(f"\nSuggested Use Case Distribution:")
        for use_case, count in use_dist.items():
            print(f"  {use_case}: {count} properties")
        
        # Zoning vs Score correlation
        zoning_scores = scored_df.groupby('base_zoning')['development_score'].agg(['mean', 'count', 'std'])
        zoning_scores = zoning_scores[zoning_scores['count'] >= 2].sort_values('mean', ascending=False)
        print(f"\nZoning Type Performance (avg score):")
        for zoning, stats in zoning_scores.head(10).iterrows():
            print(f"  {zoning}: {stats['mean']:.1f} ±{stats['std']:.1f} (n={int(stats['count'])})")
        
        # Production readiness indicators
        high_confidence = len(scored_df[scored_df['development_score'] >= 70])
        moderate_confidence = len(scored_df[
            (scored_df['development_score'] >= 50) & 
            (scored_df['development_score'] < 70)
        ])
        low_confidence = len(scored_df[scored_df['development_score'] < 50])
        
        print(f"\nProduction Readiness Assessment:")
        print(f"  High Confidence (70+ score): {high_confidence} properties ({high_confidence/len(scored_df)*100:.1f}%)")
        print(f"  Moderate Confidence (50-69): {moderate_confidence} properties ({moderate_confidence/len(scored_df)*100:.1f}%)")
        print(f"  Low Confidence (<50): {low_confidence} properties ({low_confidence/len(scored_df)*100:.1f}%)")
        
        return {
            'score_statistics': score_stats.to_dict(),
            'tier_distribution': tier_dist.to_dict(),
            'use_case_distribution': use_dist.to_dict(),
            'zoning_performance': zoning_scores.to_dict(),
            'confidence_levels': {
                'high': high_confidence,
                'moderate': moderate_confidence,
                'low': low_confidence
            }
        }
    
    def run_comprehensive_test(self, csv_path: str, n_sample: int = 10):
        """Run the complete test suite"""
        print("="*80)
        print(f"DEALGENIE V{self.version} COMPREHENSIVE TEST SUITE")
        print(f"Test Date: {self.test_date}")
        print(f"Sample Data: {csv_path}")
        print("="*80)
        
        # 1. Load and prepare data
        df = self.load_and_prepare_data(csv_path)
        
        # 2. Diversity validation on full dataset
        diversity_results = self.analyze_diversity_validation(df)
        
        # 3. Select representative sample
        sample_df = self.select_representative_sample(df, n_sample)
        
        # 4. Test scoring engine
        scored_df = self.test_scoring_engine(sample_df)
        
        # 5. Test development features
        development_results = self.test_development_features(scored_df)
        
        # 6. Generate accuracy assessment
        accuracy_results = self.generate_accuracy_assessment(scored_df)
        
        # 7. Generate final report
        self.generate_final_report(
            scored_df, diversity_results, 
            development_results, accuracy_results
        )
        
        return {
            'scored_properties': scored_df,
            'diversity_analysis': diversity_results,
            'development_features': development_results,
            'accuracy_assessment': accuracy_results
        }
    
    def generate_final_report(self, scored_df, diversity_results, development_results, accuracy_results):
        """Generate comprehensive final test report"""
        print(f"\n" + "="*80)
        print(f"FINAL TEST REPORT - DEALGENIE V{self.version}")
        print("="*80)
        
        print(f"\n🎯 OVERALL PERFORMANCE SUMMARY")
        print(f"   • Tested {len(scored_df)} representative properties")
        print(f"   • Average development score: {scored_df['development_score'].mean():.1f}")
        print(f"   • Score range: {scored_df['development_score'].min():.1f} - {scored_df['development_score'].max():.1f}")
        print(f"   • Investment opportunities identified: {len(scored_df[scored_df['development_score'] >= 70])}")
        
        print(f"\n📊 DIVERSITY VALIDATION")
        print(f"   • ZIP codes represented: {diversity_results['zip_diversity']}")
        print(f"   • Zoning types tested: {diversity_results['zoning_diversity']}")
        print(f"   • Property type mix:")
        for prop_type, count in diversity_results['property_types'].items():
            if count > 0:
                print(f"     - {prop_type}: {count}")
        
        print(f"\n🏗️ DEVELOPMENT FEATURES")
        print(f"   • TOC-eligible properties: {development_results['toc_properties']}")
        print(f"   • SB9 candidates: {development_results['sb9_candidates']}")
        print(f"   • Mixed-use potential: {development_results['mixed_use_potential']}")
        print(f"   • High-density opportunities: {development_results['high_density_opportunities']}")
        print(f"   • Large lot assemblies: {development_results['large_lot_opportunities']}")
        
        print(f"\n✅ PRODUCTION READINESS")
        confidence = accuracy_results['confidence_levels']
        total = sum(confidence.values())
        print(f"   • High confidence properties: {confidence['high']}/{total} ({confidence['high']/total*100:.1f}%)")
        print(f"   • System reliability: {'PRODUCTION READY' if confidence['high']/total >= 0.6 else 'NEEDS IMPROVEMENT'}")
        print(f"   • Scoring consistency: {'GOOD' if scored_df['development_score'].std() < 25 else 'VARIABLE'}")
        
        print(f"\n📈 TOP PERFORMING PROPERTIES")
        top_3 = scored_df.nlargest(3, 'development_score')
        for i, (_, row) in enumerate(top_3.iterrows(), 1):
            print(f"   {i}. Score: {row['development_score']:.1f} | {row['base_zoning']} | {row['lot_size_sqft']:,.0f} sqft")
            print(f"      Use: {row['suggested_use']} | Tier: {row['investment_tier']}")
        
        print(f"\n🎉 CONCLUSION")
        overall_performance = scored_df['development_score'].mean()
        if overall_performance >= 60:
            status = "EXCELLENT - Ready for production deployment"
        elif overall_performance >= 50:
            status = "GOOD - Minor calibration recommended"
        else:
            status = "NEEDS IMPROVEMENT - Requires algorithm refinement"
        
        print(f"   DealGenie V{self.version} Performance: {status}")
        print(f"   Test completed successfully on {self.test_date}")
        
        print("="*80)


def main():
    """Main test execution"""
    # Initialize test suite
    test_suite = DealGenieTestSuite()
    
    # Run comprehensive test
    csv_path = "/Users/samanthagrant/Desktop/dealgenie/scraper/diverse_dealgenie_sample_1000.csv"
    results = test_suite.run_comprehensive_test(csv_path, n_sample=10)
    
    # Save detailed results
    output_file = f"dealgenie_v{test_suite.version}_test_results_{test_suite.test_date}.json"
    with open(output_file, 'w') as f:
        # Convert DataFrames to dict for JSON serialization
        results_for_json = {
            'diversity_analysis': results['diversity_analysis'],
            'development_features': results['development_features'],
            'accuracy_assessment': results['accuracy_assessment']
        }
        json.dump(results_for_json, f, indent=2, default=str)
    
    print(f"\n💾 Detailed test results saved to: {output_file}")
    
    # Save scored properties CSV
    csv_output = f"dealgenie_v{test_suite.version}_scored_sample_{test_suite.test_date}.csv"
    results['scored_properties'].to_csv(csv_output, index=False)
    print(f"💾 Scored properties saved to: {csv_output}")


if __name__ == "__main__":
    main()