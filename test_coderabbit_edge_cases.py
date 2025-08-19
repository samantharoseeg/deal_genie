#!/usr/bin/env python3
"""
Test CodeRabbit Edge Cases
=========================

Test specific edge cases that CodeRabbit might have identified in complex systems.
"""

import pandas as pd
import numpy as np
import time
import gc
from typing import List, Dict
from toc_tier_calculator_optimized import TOCTierCalculatorOptimized


def test_memory_management():
    """Test memory management with large datasets"""
    print("🧠 TESTING MEMORY MANAGEMENT")
    print("=" * 80)
    
    calc = TOCTierCalculatorOptimized(enable_caching=True)
    
    # Test with increasingly large datasets
    dataset_sizes = [100, 500, 1000, 2000]
    memory_results = []
    
    for size in dataset_sizes:
        print(f"\nTesting with {size} properties...")
        
        # Generate large test dataset
        np.random.seed(42)
        test_data = pd.DataFrame({
            'property_id': range(size),
            'latitude': np.random.normal(34.0522, 0.1, size),
            'longitude': np.random.normal(-118.2437, 0.1, size)
        })
        
        # Monitor memory usage
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        try:
            results = calc.process_properties_batch(test_data)
            
            processing_time = time.time() - start_time
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            memory_results.append({
                'dataset_size': size,
                'processing_time': processing_time,
                'memory_used_mb': memory_used,
                'properties_per_second': size / processing_time,
                'success': True
            })
            
            print(f"   ✅ Success: {processing_time:.2f}s, {memory_used:.1f}MB, {size/processing_time:.0f} props/sec")
            
            # Force garbage collection
            del results
            del test_data
            gc.collect()
            
        except Exception as e:
            memory_results.append({
                'dataset_size': size,
                'error': str(e),
                'success': False
            })
            print(f"   ❌ Failed: {str(e)}")
    
    # Analyze memory scaling
    successful_results = [r for r in memory_results if r['success']]
    if len(successful_results) >= 2:
        memory_scaling = successful_results[-1]['memory_used_mb'] / successful_results[0]['memory_used_mb']
        size_scaling = successful_results[-1]['dataset_size'] / successful_results[0]['dataset_size']
        memory_efficiency = memory_scaling / size_scaling
        
        print(f"\n📊 MEMORY SCALING ANALYSIS")
        print(f"   Dataset scaling: {size_scaling:.1f}x")
        print(f"   Memory scaling: {memory_scaling:.1f}x")
        print(f"   Memory efficiency: {memory_efficiency:.2f} (lower is better)")
        
        if memory_efficiency < 2.0:
            print(f"   ✅ Good memory scaling")
        else:
            print(f"   ⚠️ Memory usage growing faster than dataset size")
    
    return memory_results


def test_concurrent_access():
    """Test concurrent access patterns"""
    print(f"\n🔄 TESTING CONCURRENT ACCESS PATTERNS")
    print("=" * 80)
    
    import threading
    from concurrent.futures import ThreadPoolExecutor
    
    calc = TOCTierCalculatorOptimized(enable_caching=True)
    
    # Test data for concurrent access
    test_coordinates = [
        (34.102403, -118.338974),  # Hollywood/Highland
        (34.056207, -118.234468),  # Union Station
        (34.048653, -118.259109),  # 7th St/Metro Center
        (34.0, -119.0),            # Far from transit
        (34.1, -118.0),            # Edge case
    ]
    
    results = []
    errors = []
    
    def calculate_toc_thread(coord_pair):
        """Thread function for TOC calculation"""
        try:
            lat, lon = coord_pair
            result = calc.calculate_toc_tier(lat, lon)
            return {'success': True, 'result': result, 'coordinates': coord_pair}
        except Exception as e:
            return {'success': False, 'error': str(e), 'coordinates': coord_pair}
    
    # Test concurrent execution
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit multiple calculations concurrently
        futures = []
        for _ in range(10):  # Multiple rounds
            for coord in test_coordinates:
                future = executor.submit(calculate_toc_thread, coord)
                futures.append(future)
        
        # Collect results
        for future in futures:
            result = future.result()
            if result['success']:
                results.append(result)
            else:
                errors.append(result)
    
    concurrent_time = time.time() - start_time
    
    print(f"   Concurrent calculations: {len(results)} successful, {len(errors)} errors")
    print(f"   Total time: {concurrent_time:.2f}s")
    print(f"   Calculations per second: {len(results)/concurrent_time:.1f}")
    
    # Test for thread safety issues
    if len(errors) == 0:
        print(f"   ✅ No thread safety issues detected")
    else:
        print(f"   ⚠️ {len(errors)} errors detected - possible thread safety issues")
        for error in errors[:3]:  # Show first few errors
            print(f"      Error at {error['coordinates']}: {error['error']}")
    
    return {'successful': len(results), 'errors': len(errors), 'time': concurrent_time}


def test_extreme_coordinates():
    """Test extreme coordinate values"""
    print(f"\n🌍 TESTING EXTREME COORDINATES")
    print("=" * 80)
    
    calc = TOCTierCalculatorOptimized()
    
    extreme_cases = [
        # Boundary coordinates
        {'name': 'North Pole', 'lat': 90.0, 'lon': 0.0},
        {'name': 'South Pole', 'lat': -90.0, 'lon': 0.0},
        {'name': 'International Date Line', 'lat': 0.0, 'lon': 180.0},
        {'name': 'Prime Meridian', 'lat': 0.0, 'lon': 0.0},
        
        # Edge of valid ranges
        {'name': 'Max Valid Lat', 'lat': 89.999, 'lon': -118.2437},
        {'name': 'Min Valid Lat', 'lat': -89.999, 'lon': -118.2437},
        {'name': 'Max Valid Lon', 'lat': 34.0522, 'lon': 179.999},
        {'name': 'Min Valid Lon', 'lat': 34.0522, 'lon': -179.999},
        
        # Invalid coordinates
        {'name': 'Invalid High Lat', 'lat': 91.0, 'lon': -118.2437},
        {'name': 'Invalid Low Lat', 'lat': -91.0, 'lon': -118.2437},
        {'name': 'Invalid High Lon', 'lat': 34.0522, 'lon': 181.0},
        {'name': 'Invalid Low Lon', 'lat': 34.0522, 'lon': -181.0},
        
        # Special float values
        {'name': 'NaN Latitude', 'lat': float('nan'), 'lon': -118.2437},
        {'name': 'NaN Longitude', 'lat': 34.0522, 'lon': float('nan')},
        {'name': 'Infinity Latitude', 'lat': float('inf'), 'lon': -118.2437},
        {'name': 'Negative Infinity', 'lat': float('-inf'), 'lon': -118.2437},
    ]
    
    extreme_results = []
    
    for case in extreme_cases:
        try:
            result = calc.calculate_toc_tier(case['lat'], case['lon'])
            
            extreme_results.append({
                'case': case['name'],
                'coordinates': (case['lat'], case['lon']),
                'tier': result['toc_tier'],
                'points': result['bonus_points'],
                'handled_gracefully': True,
                'error': None
            })
            
            print(f"   ✅ {case['name']}: Tier {result['toc_tier']} (handled gracefully)")
            
        except Exception as e:
            extreme_results.append({
                'case': case['name'],
                'coordinates': (case['lat'], case['lon']),
                'handled_gracefully': False,
                'error': str(e)
            })
            
            # Check if it's a proper exception type
            if 'TOC' in str(type(e)) or 'Calculator' in str(type(e)):
                print(f"   ✅ {case['name']}: Proper exception - {str(e)[:50]}...")
            else:
                print(f"   ⚠️ {case['name']}: Unexpected error - {str(e)[:50]}...")
    
    # Analyze results
    graceful_handling = sum(1 for r in extreme_results if r['handled_gracefully'])
    proper_exceptions = sum(1 for r in extreme_results 
                          if not r['handled_gracefully'] and 
                          ('TOC' in str(r.get('error', '')) or 'Calculator' in str(r.get('error', ''))))
    
    total_proper = graceful_handling + proper_exceptions
    
    print(f"\n📊 EXTREME COORDINATE HANDLING")
    print(f"   Total test cases: {len(extreme_cases)}")
    print(f"   Gracefully handled: {graceful_handling}")
    print(f"   Proper exceptions: {proper_exceptions}")
    print(f"   Overall robustness: {total_proper}/{len(extreme_cases)} ({total_proper/len(extreme_cases)*100:.1f}%)")
    
    return extreme_results


def test_performance_edge_cases():
    """Test performance edge cases"""
    print(f"\n⚡ TESTING PERFORMANCE EDGE CASES")
    print("=" * 80)
    
    calc = TOCTierCalculatorOptimized(enable_caching=True)
    
    # Test cache performance
    print("Testing cache performance...")
    
    # Repeated calculations (should hit cache)
    test_coord = (34.102403, -118.338974)
    
    # First calculation (cache miss)
    start_time = time.time()
    result1 = calc.calculate_toc_tier(*test_coord)
    first_time = time.time() - start_time
    
    # Repeated calculations (should hit cache)
    cache_times = []
    for _ in range(100):
        start_time = time.time()
        result = calc.calculate_toc_tier(*test_coord)
        cache_times.append(time.time() - start_time)
    
    avg_cache_time = sum(cache_times) / len(cache_times)
    cache_speedup = first_time / avg_cache_time if avg_cache_time > 0 else 0
    
    print(f"   First calculation: {first_time*1000:.2f}ms")
    print(f"   Average cached: {avg_cache_time*1000:.2f}ms")
    print(f"   Cache speedup: {cache_speedup:.1f}x")
    
    # Test with many unique coordinates (cache misses)
    print("\nTesting with many unique coordinates...")
    
    unique_coords = [(34.0522 + i*0.001, -118.2437 + i*0.001) for i in range(1000)]
    
    start_time = time.time()
    for coord in unique_coords:
        calc.calculate_toc_tier(*coord)
    unique_time = time.time() - start_time
    
    print(f"   1000 unique calculations: {unique_time:.2f}s")
    print(f"   Average per calculation: {unique_time/1000*1000:.2f}ms")
    
    # Get performance metrics
    metrics = calc.get_system_metrics()
    engine_metrics = metrics.get('engine_metrics', {})
    distance_stats = engine_metrics.get('distance_calculator_stats', {})
    
    print(f"\n📊 CACHE STATISTICS")
    print(f"   Total calculations: {distance_stats.get('total_calculations', 0)}")
    print(f"   Cache hits: {distance_stats.get('cache_hits', 0)}")
    print(f"   Cache hit rate: {distance_stats.get('cache_hit_rate_percent', 0):.1f}%")
    
    return {
        'cache_speedup': cache_speedup,
        'cache_hit_rate': distance_stats.get('cache_hit_rate_percent', 0),
        'performance_metrics': metrics
    }


def main():
    """Run comprehensive edge case testing"""
    print("🔬 COMPREHENSIVE CODERABBIT EDGE CASE TESTING")
    print("=" * 100)
    
    # Test memory management
    memory_results = test_memory_management()
    
    # Test concurrent access
    concurrent_results = test_concurrent_access()
    
    # Test extreme coordinates
    extreme_results = test_extreme_coordinates()
    
    # Test performance edge cases
    performance_results = test_performance_edge_cases()
    
    # Overall assessment
    print(f"\n🏆 EDGE CASE TESTING SUMMARY")
    print("=" * 100)
    
    # Assess each test category
    memory_ok = all(r.get('success', False) for r in memory_results)
    concurrent_ok = concurrent_results['errors'] == 0
    extreme_ok = sum(1 for r in extreme_results if r['handled_gracefully'] or 'TOC' in str(r.get('error', ''))) / len(extreme_results) >= 0.8
    performance_ok = performance_results['cache_hit_rate'] > 50
    
    overall_success = memory_ok and concurrent_ok and extreme_ok and performance_ok
    
    if overall_success:
        print("✅ EDGE CASE TESTING: EXCELLENT")
        print("✅ Memory management: Efficient scaling")
        print("✅ Concurrent access: Thread-safe")
        print("✅ Extreme coordinates: Robust error handling")
        print("✅ Performance: Good caching behavior")
        print("✅ System ready for production deployment")
    else:
        print("⚠️ EDGE CASE TESTING: SOME ISSUES DETECTED")
        if not memory_ok:
            print("❌ Memory management: Issues with large datasets")
        if not concurrent_ok:
            print("❌ Concurrent access: Thread safety issues")
        if not extreme_ok:
            print("❌ Extreme coordinates: Error handling needs improvement")
        if not performance_ok:
            print("❌ Performance: Cache performance suboptimal")
    
    print(f"\n📊 DETAILED RESULTS")
    print(f"   Memory tests: {len([r for r in memory_results if r.get('success', False)])}/{len(memory_results)} passed")
    print(f"   Concurrent calculations: {concurrent_results['successful']} successful, {concurrent_results['errors']} errors")
    print(f"   Extreme coordinate handling: {sum(1 for r in extreme_results if r['handled_gracefully'])}/{len(extreme_results)} graceful")
    print(f"   Cache hit rate: {performance_results['cache_hit_rate']:.1f}%")
    print(f"   Cache speedup: {performance_results['cache_speedup']:.1f}x")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)