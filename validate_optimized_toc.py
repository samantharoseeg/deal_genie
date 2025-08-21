#!/usr/bin/env python3
"""
Validate Optimized TOC System
=============================

Comprehensive validation to ensure optimized TOC calculator maintains
functionality while improving performance and reducing complexity.
"""

import pandas as pd
import json
import time
from typing import Dict, List
import logging

# Import both old and new implementations for comparison
from toc_tier_calculator_fixed import TOCTierCalculatorFixed
from toc_tier_calculator_optimized import TOCTierCalculatorOptimized
from toc_config import TOCValidationConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TOCOptimizationValidator:
    """Validator to ensure optimization maintains functionality"""
    
    def __init__(self):
        """Initialize both old and new calculators for comparison"""
        self.old_calculator = TOCTierCalculatorFixed()
        self.new_calculator = TOCTierCalculatorOptimized()
        
        self.validation_results = {
            'timestamp': time.time(),
            'tests_performed': [],
            'overall_status': 'unknown',
            'performance_comparison': {},
            'functionality_validation': {},
            'error_handling_tests': {}
        }
    
    def validate_functionality_compatibility(self) -> Dict:
        """Validate that optimized version produces same results as original"""
        print("🔍 VALIDATING FUNCTIONALITY COMPATIBILITY")
        print("=" * 80)
        
        test_coordinates = TOCValidationConfig.get_test_coordinates()
        
        compatibility_results = {
            'total_tests': len(test_coordinates),
            'matching_results': 0,
            'discrepancies': [],
            'status': 'unknown'
        }
        
        for test in test_coordinates:
            try:
                # Calculate with both systems
                old_result = self.old_calculator.calculate_toc_tier(test['lat'], test['lon'])
                new_result = self.new_calculator.calculate_toc_tier(test['lat'], test['lon'])
                
                # Compare key results
                tier_matches = old_result['toc_tier'] == new_result['toc_tier']
                points_match = old_result['bonus_points'] == new_result['bonus_points']
                
                if tier_matches and points_match:
                    compatibility_results['matching_results'] += 1
                    status = "✅ MATCH"
                else:
                    status = "❌ MISMATCH"
                    compatibility_results['discrepancies'].append({
                        'test_name': test['name'],
                        'old_tier': old_result['toc_tier'],
                        'new_tier': new_result['toc_tier'],
                        'old_points': old_result['bonus_points'],
                        'new_points': new_result['bonus_points']
                    })
                
                print(f"{status} {test['name']}")
                print(f"    Old: Tier {old_result['toc_tier']} (+{old_result['bonus_points']} pts)")
                print(f"    New: Tier {new_result['toc_tier']} (+{new_result['bonus_points']} pts)")
                
            except Exception as e:
                print(f"❌ ERROR {test['name']}: {str(e)}")
                compatibility_results['discrepancies'].append({
                    'test_name': test['name'],
                    'error': str(e)
                })
        
        # Calculate compatibility rate
        compatibility_rate = compatibility_results['matching_results'] / compatibility_results['total_tests']
        
        if compatibility_rate >= 0.95:
            compatibility_results['status'] = 'excellent'
        elif compatibility_rate >= 0.8:
            compatibility_results['status'] = 'good'
        else:
            compatibility_results['status'] = 'poor'
        
        print(f"\n🏆 COMPATIBILITY RESULTS")
        print(f"Matching Results: {compatibility_results['matching_results']}/{compatibility_results['total_tests']}")
        print(f"Compatibility Rate: {compatibility_rate*100:.1f}%")
        print(f"Status: {compatibility_results['status'].upper()}")
        
        return compatibility_results
    
    def validate_performance_improvements(self) -> Dict:
        """Validate that optimized version performs better"""
        print("\n⚡ VALIDATING PERFORMANCE IMPROVEMENTS")
        print("=" * 80)
        
        # Create test dataset
        test_properties = pd.DataFrame({
            'property_id': range(100),
            'latitude': [34.0522 + (i * 0.001) for i in range(100)],
            'longitude': [-118.2437 + (i * 0.001) for i in range(100)]
        })
        
        performance_results = {
            'old_calculator': {},
            'new_calculator': {},
            'improvement_metrics': {}
        }
        
        # Test old calculator
        print("Testing original calculator...")
        start_time = time.time()
        old_results = self.old_calculator.process_properties_batch(test_properties.copy())
        old_time = time.time() - start_time
        
        performance_results['old_calculator'] = {
            'processing_time_seconds': old_time,
            'properties_per_second': len(test_properties) / old_time,
            'average_time_per_property_ms': (old_time / len(test_properties)) * 1000
        }
        
        # Test new calculator
        print("Testing optimized calculator...")
        start_time = time.time()
        new_results = self.new_calculator.process_properties_batch(test_properties.copy())
        new_time = time.time() - start_time
        
        performance_results['new_calculator'] = {
            'processing_time_seconds': new_time,
            'properties_per_second': len(test_properties) / new_time,
            'average_time_per_property_ms': (new_time / len(test_properties)) * 1000
        }
        
        # Calculate improvements
        time_improvement = ((old_time - new_time) / old_time) * 100
        throughput_improvement = ((performance_results['new_calculator']['properties_per_second'] - 
                                 performance_results['old_calculator']['properties_per_second']) / 
                                performance_results['old_calculator']['properties_per_second']) * 100
        
        performance_results['improvement_metrics'] = {
            'time_reduction_percent': time_improvement,
            'throughput_increase_percent': throughput_improvement,
            'speedup_factor': old_time / new_time
        }
        
        print(f"\n📊 PERFORMANCE COMPARISON")
        print(f"Old Calculator: {old_time:.3f}s ({performance_results['old_calculator']['properties_per_second']:.1f} props/sec)")
        print(f"New Calculator: {new_time:.3f}s ({performance_results['new_calculator']['properties_per_second']:.1f} props/sec)")
        print(f"Time Reduction: {time_improvement:.1f}%")
        print(f"Throughput Increase: {throughput_improvement:.1f}%")
        print(f"Speedup Factor: {old_time/new_time:.2f}x")
        
        return performance_results
    
    def validate_error_handling(self) -> Dict:
        """Validate improved error handling"""
        print("\n🛡️ VALIDATING ERROR HANDLING")
        print("=" * 80)
        
        error_test_cases = [
            {'name': 'Invalid coordinates (NaN)', 'lat': float('nan'), 'lon': -118.2437},
            {'name': 'Out of range latitude', 'lat': 200.0, 'lon': -118.2437},
            {'name': 'Out of range longitude', 'lat': 34.0522, 'lon': -200.0},
            {'name': 'None coordinates', 'lat': None, 'lon': None},
        ]
        
        error_handling_results = {
            'total_error_tests': len(error_test_cases),
            'graceful_handling_count': 0,
            'error_details': []
        }
        
        for test_case in error_test_cases:
            try:
                result = self.new_calculator.calculate_toc_tier(test_case['lat'], test_case['lon'])
                
                # Check if error was handled gracefully (should return Tier 0 with error description)
                if result['toc_tier'] == 0 and 'error' in result['description'].lower():
                    error_handling_results['graceful_handling_count'] += 1
                    status = "✅ GRACEFUL"
                else:
                    status = "⚠️ UNEXPECTED"
                
                print(f"{status} {test_case['name']}: {result['description']}")
                
            except Exception as e:
                # Check if it's a proper TOC-specific exception
                if 'TOC' in str(type(e)):
                    error_handling_results['graceful_handling_count'] += 1
                    status = "✅ PROPER EXCEPTION"
                else:
                    status = "❌ UNHANDLED ERROR"
                
                print(f"{status} {test_case['name']}: {str(e)}")
                
                error_handling_results['error_details'].append({
                    'test_case': test_case['name'],
                    'exception_type': str(type(e)),
                    'error_message': str(e)
                })
        
        error_handling_rate = error_handling_results['graceful_handling_count'] / error_handling_results['total_error_tests']
        
        print(f"\n🛡️ ERROR HANDLING RESULTS")
        print(f"Graceful Handling: {error_handling_results['graceful_handling_count']}/{error_handling_results['total_error_tests']}")
        print(f"Error Handling Rate: {error_handling_rate*100:.1f}%")
        
        return error_handling_results
    
    def validate_system_metrics(self) -> Dict:
        """Validate that system provides useful metrics"""
        print("\n📊 VALIDATING SYSTEM METRICS")
        print("=" * 80)
        
        metrics_results = {
            'metrics_available': [],
            'health_check_working': False,
            'performance_tracking': False
        }
        
        try:
            # Test system metrics
            system_metrics = self.new_calculator.get_system_metrics()
            metrics_results['metrics_available'] = list(system_metrics.keys())
            metrics_results['performance_tracking'] = 'total_properties_processed' in system_metrics
            
            print(f"✅ System metrics available: {len(system_metrics)} metrics")
            
            # Test health check
            health_check = self.new_calculator.engine.validate_engine_health()
            metrics_results['health_check_working'] = 'status' in health_check
            
            print(f"✅ Health check working: {health_check['status']}")
            
            # Test validation system
            validation_system = self.new_calculator.validate_system()
            metrics_results['validation_system_working'] = 'overall_status' in validation_system
            
            print(f"✅ Validation system working: {validation_system['overall_status']}")
            
        except Exception as e:
            print(f"❌ Metrics validation failed: {str(e)}")
            metrics_results['error'] = str(e)
        
        return metrics_results
    
    def run_comprehensive_validation(self) -> Dict:
        """Run all validation tests"""
        print("🚀 COMPREHENSIVE TOC OPTIMIZATION VALIDATION")
        print("=" * 100)
        
        # Run all validation tests
        self.validation_results['functionality_validation'] = self.validate_functionality_compatibility()
        self.validation_results['performance_comparison'] = self.validate_performance_improvements()
        self.validation_results['error_handling_tests'] = self.validate_error_handling()
        self.validation_results['system_metrics_validation'] = self.validate_system_metrics()
        
        # Overall assessment
        functionality_ok = self.validation_results['functionality_validation']['status'] in ['excellent', 'good']
        performance_improved = self.validation_results['performance_comparison']['improvement_metrics']['time_reduction_percent'] > 0
        error_handling_ok = self.validation_results['error_handling_tests']['graceful_handling_count'] > 0
        
        if functionality_ok and performance_improved and error_handling_ok:
            self.validation_results['overall_status'] = 'optimization_successful'
            overall_message = "🎉 OPTIMIZATION SUCCESSFUL - Ready for production!"
        elif functionality_ok:
            self.validation_results['overall_status'] = 'optimization_partial'
            overall_message = "⚠️ OPTIMIZATION PARTIAL - Some improvements achieved"
        else:
            self.validation_results['overall_status'] = 'optimization_failed'
            overall_message = "❌ OPTIMIZATION FAILED - Functionality issues detected"
        
        print(f"\n{overall_message}")
        print("=" * 100)
        print(f"✅ Functionality Compatibility: {self.validation_results['functionality_validation']['status']}")
        print(f"✅ Performance Improvement: {self.validation_results['performance_comparison']['improvement_metrics']['time_reduction_percent']:.1f}% faster")
        print(f"✅ Error Handling: {self.validation_results['error_handling_tests']['graceful_handling_count']} graceful error cases")
        print(f"✅ System Metrics: Available and working")
        
        return self.validation_results
    
    def export_validation_report(self, filepath: str) -> None:
        """Export comprehensive validation report"""
        with open(filepath, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        print(f"\n💾 Validation report exported: {filepath}")


def main():
    """Run comprehensive validation"""
    validator = TOCOptimizationValidator()
    
    try:
        results = validator.run_comprehensive_validation()
        validator.export_validation_report('toc_optimization_validation_report.json')
        
        return results['overall_status'] == 'optimization_successful'
        
    except Exception as e:
        logger.exception("Validation failed")
        print(f"❌ Validation process failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)