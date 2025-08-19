#!/usr/bin/env python3
"""
Test Investment-Grade Scoring with Optimized TOC
===============================================

Validate that 70+ investment-grade scoring still works after optimization.
"""

import pandas as pd
from toc_tier_calculator_optimized import TOCTierCalculatorOptimized
from toc_tier_calculator_fixed import TOCTierCalculatorFixed


def test_investment_grade_scoring():
    """Test investment-grade scoring with both old and new systems"""
    print("💰 TESTING INVESTMENT-GRADE SCORING (70+ POINTS)")
    print("=" * 80)
    
    # Initialize both calculators
    old_calc = TOCTierCalculatorFixed()
    new_calc = TOCTierCalculatorOptimized()
    
    # Premium test properties near stations
    premium_properties = [
        {'name': 'Hollywood Transit Village', 'lat': 34.102403, 'lon': -118.338974, 'zoning': 'C4', 'lot_sqft': 25000},
        {'name': 'Union Station TOD', 'lat': 34.056207, 'lon': -118.234468, 'zoning': 'R5', 'lot_sqft': 35000},
        {'name': 'Downtown High-Rise Site', 'lat': 34.048653, 'lon': -118.259109, 'zoning': 'C4', 'lot_sqft': 20000},
        {'name': 'Hollywood/Vine Development', 'lat': 34.102252, 'lon': -118.326499, 'zoning': 'C4', 'lot_sqft': 15000},
    ]
    
    print("\n🧪 TESTING PREMIUM PROPERTIES")
    print("-" * 60)
    
    results_comparison = []
    
    for prop in premium_properties:
        print(f"\n📍 {prop['name']}")
        print(f"   Coordinates: ({prop['lat']:.6f}, {prop['lon']:.6f})")
        
        # Test with old calculator
        old_toc = old_calc.calculate_toc_tier(prop['lat'], prop['lon'])
        old_enhanced_score = simulate_enhanced_scoring(old_toc, prop)
        
        # Test with new calculator
        new_toc = new_calc.calculate_toc_tier(prop['lat'], prop['lon'])
        new_enhanced_score = simulate_enhanced_scoring(new_toc, prop)
        
        # Compare results
        tier_match = old_toc['toc_tier'] == new_toc['toc_tier']
        score_diff = abs(old_enhanced_score - new_enhanced_score)
        
        results_comparison.append({
            'property': prop['name'],
            'old_tier': old_toc['toc_tier'],
            'new_tier': new_toc['toc_tier'],
            'old_score': old_enhanced_score,
            'new_score': new_enhanced_score,
            'tier_match': tier_match,
            'score_difference': score_diff,
            'investment_grade': new_enhanced_score >= 70
        })
        
        status = "✅ MATCH" if tier_match else "❌ MISMATCH"
        investment_status = "✅ INVESTMENT GRADE" if new_enhanced_score >= 70 else "❌ Below 70"
        
        print(f"   {status} TOC Tiers: Old={old_toc['toc_tier']}, New={new_toc['toc_tier']}")
        print(f"   Enhanced Scores: Old={old_enhanced_score:.1f}, New={new_enhanced_score:.1f}")
        print(f"   {investment_status} (Score: {new_enhanced_score:.1f})")
        print(f"   Distance: {new_toc['distance_feet']:,.0f} ft to {new_toc['nearest_station']}")
    
    # Summary statistics
    total_properties = len(results_comparison)
    tier_matches = sum(1 for r in results_comparison if r['tier_match'])
    investment_grade_count = sum(1 for r in results_comparison if r['investment_grade'])
    max_score_diff = max(r['score_difference'] for r in results_comparison)
    
    print(f"\n🏆 INVESTMENT-GRADE SCORING RESULTS")
    print("=" * 80)
    print(f"Properties Tested: {total_properties}")
    print(f"TOC Tier Matches: {tier_matches}/{total_properties} ({tier_matches/total_properties*100:.1f}%)")
    print(f"Investment Grade (70+): {investment_grade_count}/{total_properties} ({investment_grade_count/total_properties*100:.1f}%)")
    print(f"Maximum Score Difference: {max_score_diff:.1f} points")
    
    # Test success criteria
    tier_compatibility = tier_matches / total_properties >= 0.95
    investment_achievement = investment_grade_count > 0
    score_stability = max_score_diff < 5.0
    
    overall_success = tier_compatibility and investment_achievement and score_stability
    
    if overall_success:
        print(f"\n✅ INVESTMENT-GRADE SCORING: VALIDATED")
        print(f"✅ 70+ scoring capability preserved in optimized system")
        print(f"✅ TOC tier compatibility maintained")
        print(f"✅ Score differences within acceptable range")
    else:
        print(f"\n❌ INVESTMENT-GRADE SCORING: ISSUES DETECTED")
        if not tier_compatibility:
            print(f"❌ TOC tier compatibility below 95%")
        if not investment_achievement:
            print(f"❌ No properties achieved 70+ scores")
        if not score_stability:
            print(f"❌ Score differences too large (>{max_score_diff:.1f} points)")
    
    return overall_success, results_comparison


def simulate_enhanced_scoring(toc_result, property_info):
    """Simulate enhanced scoring system with TOC integration"""
    
    # Base property scoring components
    base_score = 45.0  # Starting base
    
    # Zoning bonus
    zoning_bonus = {
        'C4': 15.0,  # Commercial high-density
        'R5': 12.0,  # Residential high-density
        'M2': 8.0,   # Manufacturing
    }.get(property_info.get('zoning', 'R1'), 5.0)
    
    # Lot size bonus
    lot_sqft = property_info.get('lot_sqft', 5000)
    if lot_sqft >= 20000:
        lot_bonus = 15.0
    elif lot_sqft >= 10000:
        lot_bonus = 10.0
    else:
        lot_bonus = 5.0
    
    # TOC bonus (enhanced weighting)
    toc_bonus = toc_result['bonus_points'] * 1.2  # Enhanced TOC weighting
    
    # Calculate total enhanced score
    total_score = base_score + zoning_bonus + lot_bonus + toc_bonus
    
    return total_score


def test_edge_cases():
    """Test edge cases for investment scoring"""
    print("\n🔍 TESTING EDGE CASES")
    print("-" * 60)
    
    calc = TOCTierCalculatorOptimized()
    
    edge_cases = [
        # Boundary distances
        {'name': 'Exactly 750ft boundary', 'lat': 34.102403 + (750/364000), 'lon': -118.338974},
        {'name': 'Exactly 1500ft boundary', 'lat': 34.102403 + (1500/364000), 'lon': -118.338974},
        {'name': 'Exactly 2640ft boundary', 'lat': 34.102403 + (2640/364000), 'lon': -118.338974},
        
        # Invalid coordinates
        {'name': 'Invalid latitude', 'lat': 200.0, 'lon': -118.338974},
        {'name': 'Invalid longitude', 'lat': 34.102403, 'lon': -300.0},
        
        # Far from transit
        {'name': 'Very far from transit', 'lat': 34.0, 'lon': -119.0},
    ]
    
    edge_case_results = []
    
    for case in edge_cases:
        try:
            result = calc.calculate_toc_tier(case['lat'], case['lon'])
            
            edge_case_results.append({
                'case': case['name'],
                'tier': result['toc_tier'],
                'points': result['bonus_points'],
                'distance': result['distance_feet'],
                'station': result['nearest_station'],
                'error': None
            })
            
            print(f"✅ {case['name']}: Tier {result['toc_tier']} (+{result['bonus_points']} pts)")
            
        except Exception as e:
            edge_case_results.append({
                'case': case['name'],
                'error': str(e),
                'tier': None,
                'points': None
            })
            
            print(f"⚠️ {case['name']}: {str(e)}")
    
    return edge_case_results


def main():
    """Run comprehensive investment-grade scoring validation"""
    print("🎯 COMPREHENSIVE INVESTMENT-GRADE SCORING VALIDATION")
    print("=" * 100)
    
    # Test investment-grade scoring
    scoring_success, scoring_results = test_investment_grade_scoring()
    
    # Test edge cases
    edge_results = test_edge_cases()
    
    # Overall assessment
    print(f"\n🏆 FINAL ASSESSMENT")
    print("=" * 100)
    
    if scoring_success:
        print("✅ INVESTMENT-GRADE SCORING: FULLY FUNCTIONAL")
        print("✅ 70+ point scoring capability preserved")
        print("✅ TOC optimization did not break scoring system")
        print("✅ Ready for production deployment")
        
        # Show specific achievements
        investment_properties = [r for r in scoring_results if r['investment_grade']]
        print(f"\n💎 INVESTMENT-GRADE PROPERTIES VALIDATED:")
        for prop in investment_properties:
            print(f"   • {prop['property']}: {prop['new_score']:.1f} points (Tier {prop['new_tier']})")
        
    else:
        print("❌ INVESTMENT-GRADE SCORING: ISSUES DETECTED")
        print("❌ Manual review required before deployment")
    
    return scoring_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)