#!/usr/bin/env python3
"""
Test File Output Compatibility
==============================

Verify that optimized TOC system generates all expected file outputs correctly.
"""

import pandas as pd
import json
import os
from pathlib import Path
from toc_tier_calculator_optimized import TOCTierCalculatorOptimized
from toc_tier_calculator_fixed import TOCTierCalculatorFixed


def test_csv_output_compatibility():
    """Test that CSV outputs are compatible"""
    print("📊 TESTING CSV OUTPUT COMPATIBILITY")
    print("=" * 80)
    
    # Create test data
    test_properties = pd.DataFrame({
        'property_id': range(1, 11),
        'site_address': [f"{100+i} Test St" for i in range(10)],
        'latitude': [34.0522 + (i * 0.01) for i in range(10)],
        'longitude': [-118.2437 + (i * 0.01) for i in range(10)],
        'zoning': ['C4', 'R5', 'M2'] * 3 + ['C4'],
        'lot_sqft': [5000 + (i * 1000) for i in range(10)]
    })
    
    # Process with both systems
    old_calc = TOCTierCalculatorFixed()
    new_calc = TOCTierCalculatorOptimized()
    
    print("Processing with original calculator...")
    old_results = old_calc.process_properties_batch(test_properties.copy())
    
    print("Processing with optimized calculator...")
    new_results = new_calc.process_properties_batch(test_properties.copy())
    
    # Compare output structures
    print(f"\n🔍 COMPARING OUTPUT STRUCTURES")
    print("-" * 60)
    
    # Check column presence
    old_toc_cols = [col for col in old_results.columns if col.startswith('fixed_toc_')]
    new_toc_cols = [col for col in new_results.columns if col.startswith('toc_')]
    
    print(f"Original TOC columns: {len(old_toc_cols)}")
    print(f"Optimized TOC columns: {len(new_toc_cols)}")
    
    # Map column names (old has 'fixed_toc_' prefix, new has 'toc_' prefix)
    column_mapping = {
        'fixed_toc_toc_tier': 'toc_toc_tier',
        'fixed_toc_bonus_points': 'toc_bonus_points',
        'fixed_toc_description': 'toc_description',
        'fixed_toc_nearest_station': 'toc_nearest_station',
        'fixed_toc_distance_feet': 'toc_distance_feet',
        'fixed_toc_station_type': 'toc_station_type',
        'fixed_toc_station_line': 'toc_station_line'
    }
    
    compatibility_results = {
        'column_compatibility': True,
        'data_compatibility': True,
        'tier_matches': 0,
        'total_properties': len(test_properties),
        'differences': []
    }
    
    # Check data compatibility
    for old_col, new_col in column_mapping.items():
        if old_col in old_results.columns and new_col in new_results.columns:
            # Compare tier values (most important)
            if 'toc_tier' in old_col:
                tier_matches = (old_results[old_col] == new_results[new_col]).sum()
                compatibility_results['tier_matches'] = tier_matches
                
                print(f"✅ {old_col} vs {new_col}: {tier_matches}/{len(test_properties)} matches")
                
                # Check for differences
                mask = old_results[old_col] != new_results[new_col]
                if mask.any():
                    differences = test_properties.loc[mask, ['property_id', 'latitude', 'longitude']].copy()
                    differences['old_tier'] = old_results.loc[mask, old_col]
                    differences['new_tier'] = new_results.loc[mask, new_col]
                    compatibility_results['differences'].extend(differences.to_dict('records'))
        else:
            compatibility_results['column_compatibility'] = False
            print(f"❌ Missing column: {old_col} or {new_col}")
    
    # Export test results
    old_results.to_csv('test_output_original.csv', index=False)
    new_results.to_csv('test_output_optimized.csv', index=False)
    
    print(f"\n💾 Test files generated:")
    print(f"   - test_output_original.csv ({len(old_results)} rows)")
    print(f"   - test_output_optimized.csv ({len(new_results)} rows)")
    
    return compatibility_results


def test_json_output_compatibility():
    """Test JSON output compatibility"""
    print(f"\n📋 TESTING JSON OUTPUT COMPATIBILITY")
    print("=" * 80)
    
    calc = TOCTierCalculatorOptimized()
    
    # Test individual calculation output
    test_coords = [
        {'name': 'Hollywood/Highland', 'lat': 34.102403, 'lon': -118.338974},
        {'name': 'Far from transit', 'lat': 34.0, 'lon': -119.0}
    ]
    
    json_results = []
    
    for coord in test_coords:
        result = calc.calculate_toc_tier(coord['lat'], coord['lon'])
        json_results.append({
            'property_name': coord['name'],
            'coordinates': [coord['lat'], coord['lon']],
            'toc_result': result
        })
        
        print(f"✅ {coord['name']}: Tier {result['toc_tier']} JSON output generated")
    
    # Export JSON results
    with open('test_toc_results.json', 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 JSON test file generated: test_toc_results.json")
    
    # Test system metrics JSON
    metrics = calc.get_system_metrics()
    with open('test_system_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    print(f"💾 System metrics JSON generated: test_system_metrics.json")
    
    return json_results


def test_configuration_export():
    """Test configuration export functionality"""
    print(f"\n⚙️ TESTING CONFIGURATION EXPORT")
    print("=" * 80)
    
    calc = TOCTierCalculatorOptimized()
    
    try:
        # Export configuration
        calc.export_configuration('test_toc_config.json')
        
        # Verify file exists and is valid JSON
        if os.path.exists('test_toc_config.json'):
            with open('test_toc_config.json', 'r') as f:
                config_data = json.load(f)
            
            print(f"✅ Configuration export successful")
            print(f"   - Tier thresholds: {len(config_data.get('tier_thresholds', {}))} tiers")
            print(f"   - Rail stations: {len(config_data.get('stations', {}).get('rail_stations', []))}")
            print(f"   - Bus intersections: {len(config_data.get('stations', {}).get('bus_intersections', []))}")
            
            return True
        else:
            print(f"❌ Configuration file not created")
            return False
            
    except Exception as e:
        print(f"❌ Configuration export failed: {str(e)}")
        return False


def test_validation_report_generation():
    """Test validation report generation"""
    print(f"\n📋 TESTING VALIDATION REPORT GENERATION")
    print("=" * 80)
    
    calc = TOCTierCalculatorOptimized()
    
    try:
        # Generate validation report
        validation = calc.validate_system()
        
        # Export validation report
        with open('test_validation_report.json', 'w') as f:
            json.dump(validation, f, indent=2, default=str)
        
        print(f"✅ Validation report generated")
        print(f"   - Overall status: {validation['overall_status']}")
        print(f"   - Accuracy rate: {validation['accuracy_rate']*100:.1f}%")
        print(f"   - Test results: {len(validation['test_results'])} tests")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation report generation failed: {str(e)}")
        return False


def cleanup_test_files():
    """Clean up test files"""
    test_files = [
        'test_output_original.csv',
        'test_output_optimized.csv', 
        'test_toc_results.json',
        'test_system_metrics.json',
        'test_toc_config.json',
        'test_validation_report.json'
    ]
    
    print(f"\n🧹 CLEANING UP TEST FILES")
    print("-" * 40)
    
    for file in test_files:
        if os.path.exists(file):
            file_size = os.path.getsize(file)
            print(f"📁 {file}: {file_size} bytes")
            # Note: Not actually deleting files so user can inspect them
        else:
            print(f"❌ {file}: Not found")


def main():
    """Run comprehensive file output compatibility test"""
    print("📁 COMPREHENSIVE FILE OUTPUT COMPATIBILITY TEST")
    print("=" * 100)
    
    # Test CSV outputs
    csv_results = test_csv_output_compatibility()
    
    # Test JSON outputs
    json_results = test_json_output_compatibility()
    
    # Test configuration export
    config_success = test_configuration_export()
    
    # Test validation reports
    validation_success = test_validation_report_generation()
    
    # Show test files created
    cleanup_test_files()
    
    # Overall assessment
    print(f"\n🏆 FILE OUTPUT COMPATIBILITY ASSESSMENT")
    print("=" * 100)
    
    csv_compatible = (csv_results['tier_matches'] / csv_results['total_properties']) >= 0.95
    json_functional = len(json_results) > 0
    
    overall_success = csv_compatible and json_functional and config_success and validation_success
    
    if overall_success:
        print("✅ FILE OUTPUT COMPATIBILITY: EXCELLENT")
        print("✅ CSV outputs are fully compatible")
        print("✅ JSON outputs are functional")
        print("✅ Configuration export working")
        print("✅ Validation reports generating")
        print("✅ All file types supported")
        
        if csv_results['differences']:
            print(f"\n⚠️ Minor differences detected in {len(csv_results['differences'])} properties")
            print("   (This may be expected due to optimization differences)")
        
    else:
        print("❌ FILE OUTPUT COMPATIBILITY: ISSUES DETECTED")
        if not csv_compatible:
            print(f"❌ CSV compatibility below 95% ({csv_results['tier_matches']}/{csv_results['total_properties']})")
        if not json_functional:
            print(f"❌ JSON output not functional")
        if not config_success:
            print(f"❌ Configuration export failed")
        if not validation_success:
            print(f"❌ Validation report generation failed")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)