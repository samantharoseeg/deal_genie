#!/usr/bin/env python3
"""
TOC Tier Calculator - OPTIMIZED VERSION
=======================================

Optimized TOC calculator addressing CodeRabbit complexity concerns.
Refactored into modular components with improved performance and maintainability.

IMPROVEMENTS FROM CODERABBIT FEEDBACK:
- Reduced complexity through modular architecture
- Added comprehensive error handling and validation
- Implemented performance optimizations and caching
- Enhanced documentation and type hints
- Added monitoring and health checks
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Union
from dataclasses import asdict
import time

from toc_config import TOCConfig, TOCValidationConfig
from toc_tier_engine import TOCTierEngine, TOCTierEngineError, TOCResult
from toc_distance_calculator import TOCDistanceCalculatorError


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


class TOCTierCalculatorOptimized:
    """
    Optimized TOC Tier Calculator
    
    Addresses CodeRabbit complexity concerns through:
    1. Modular architecture with separated concerns
    2. Comprehensive error handling and validation
    3. Performance optimizations and caching
    4. Enhanced monitoring and observability
    5. Improved documentation and type hints
    """
    
    def __init__(self, config_file: Optional[str] = None, enable_caching: bool = True):
        """
        Initialize optimized TOC calculator
        
        Args:
            config_file: Optional path to external configuration file
            enable_caching: Enable distance calculation caching for performance
        """
        try:
            # Load configuration
            self.config = TOCConfig()
            if config_file:
                self.config.load_config(config_file)
            
            # Initialize calculation engine
            self.engine = TOCTierEngine(self.config, enable_caching=enable_caching)
            
            # Performance tracking
            self.start_time = time.time()
            self.total_properties_processed = 0
            
            logger.info("TOC Calculator Optimized initialized successfully")
            
            # Validate system health
            health = self.engine.validate_engine_health()
            if health['status'] != 'healthy':
                logger.warning(f"Engine health check issues: {health['issues']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize TOC Calculator: {str(e)}")
            raise TOCTierEngineError(f"Initialization failed: {str(e)}") from e
    
    def calculate_toc_tier(self, property_lat: float, property_lon: float) -> Dict:
        """
        Calculate TOC tier for a single property
        
        Args:
            property_lat: Property latitude
            property_lon: Property longitude
            
        Returns:
            Dictionary with TOC calculation results
            
        Raises:
            TOCTierEngineError: If calculation fails
        """
        try:
            result = self.engine.calculate_toc_tier(property_lat, property_lon)
            self.total_properties_processed += 1
            
            logger.debug(f"Calculated TOC tier {result.toc_tier} for property at "
                        f"({property_lat:.6f}, {property_lon:.6f})")
            
            return result.to_dict()
            
        except TOCTierEngineError as e:
            logger.error(f"TOC calculation failed for ({property_lat}, {property_lon}): {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in TOC calculation: {str(e)}")
            raise TOCTierEngineError(f"Calculation failed: {str(e)}") from e
    
    def process_properties_batch(self, properties_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process multiple properties with optimized batch processing
        
        Args:
            properties_df: DataFrame containing property data with coordinates
            
        Returns:
            DataFrame with TOC tier results added
            
        Raises:
            TOCTierEngineError: If batch processing fails
        """
        if properties_df.empty:
            raise TOCTierEngineError("Cannot process empty DataFrame")
        
        logger.info(f"Starting batch processing of {len(properties_df)} properties")
        batch_start_time = time.time()
        
        try:
            # Process with optimized engine
            result_df = self.engine.process_properties_batch(properties_df)
            
            # Update counters
            self.total_properties_processed += len(properties_df)
            processing_time = time.time() - batch_start_time
            
            logger.info(f"Batch processing completed in {processing_time:.2f} seconds")
            logger.info(f"Average time per property: {(processing_time/len(properties_df)*1000):.2f}ms")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise TOCTierEngineError(f"Batch processing failed: {str(e)}") from e
    
    def validate_system(self) -> Dict:
        """
        Comprehensive system validation with test coordinates
        
        Returns:
            Dictionary with validation results and system health
        """
        logger.info("Starting comprehensive system validation")
        
        validation_results = {
            'timestamp': time.time(),
            'overall_status': 'unknown',
            'test_results': [],
            'performance_metrics': {},
            'health_check': {},
            'accuracy_rate': 0.0
        }
        
        try:
            # Health check
            validation_results['health_check'] = self.engine.validate_engine_health()
            
            # Test with known coordinates
            test_coordinates = TOCValidationConfig.get_test_coordinates()
            correct_results = 0
            
            for test in test_coordinates:
                try:
                    result = self.engine.calculate_toc_tier(test['lat'], test['lon'])
                    
                    is_correct = result.toc_tier == test['expected_tier']
                    if is_correct:
                        correct_results += 1
                    
                    validation_results['test_results'].append({
                        'test_name': test['name'],
                        'expected_tier': test['expected_tier'],
                        'calculated_tier': result.toc_tier,
                        'distance_feet': result.distance_feet,
                        'nearest_station': result.nearest_station,
                        'correct': is_correct
                    })
                    
                except Exception as e:
                    logger.error(f"Validation test failed for {test['name']}: {str(e)}")
                    validation_results['test_results'].append({
                        'test_name': test['name'],
                        'error': str(e),
                        'correct': False
                    })
            
            # Calculate accuracy
            accuracy_rate = correct_results / len(test_coordinates)
            validation_results['accuracy_rate'] = accuracy_rate
            
            # Performance metrics
            validation_results['performance_metrics'] = self.engine.get_performance_metrics()
            
            # Overall status
            if accuracy_rate >= 0.8 and validation_results['health_check']['status'] == 'healthy':
                validation_results['overall_status'] = 'excellent'
            elif accuracy_rate >= 0.6:
                validation_results['overall_status'] = 'good'
            else:
                validation_results['overall_status'] = 'needs_improvement'
            
            logger.info(f"System validation completed: {validation_results['overall_status']} "
                       f"({accuracy_rate*100:.1f}% accuracy)")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"System validation failed: {str(e)}")
            validation_results['overall_status'] = 'failed'
            validation_results['error'] = str(e)
            return validation_results
    
    def get_system_metrics(self) -> Dict:
        """
        Get comprehensive system performance metrics
        
        Returns:
            Dictionary with performance and operational metrics
        """
        uptime = time.time() - self.start_time
        
        metrics = {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'total_properties_processed': self.total_properties_processed,
            'average_throughput_per_hour': (self.total_properties_processed / max(uptime / 3600, 0.001)),
            'engine_metrics': self.engine.get_performance_metrics(),
            'system_health': self.engine.validate_engine_health()
        }
        
        return metrics
    
    def export_configuration(self, filepath: str) -> None:
        """
        Export current configuration to file
        
        Args:
            filepath: Path to save configuration file
        """
        try:
            self.config.export_config(filepath)
            logger.info(f"Configuration exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {str(e)}")
            raise TOCTierEngineError(f"Configuration export failed: {str(e)}") from e
    
    def load_configuration(self, filepath: str) -> None:
        """
        Load configuration from file and reinitialize engine
        
        Args:
            filepath: Path to configuration file
        """
        try:
            self.config.load_config(filepath)
            # Reinitialize engine with new configuration
            enable_caching = self.engine.distance_calculator.enable_caching
            self.engine = TOCTierEngine(self.config, enable_caching=enable_caching)
            logger.info(f"Configuration loaded from {filepath} and engine reinitialized")
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise TOCTierEngineError(f"Configuration load failed: {str(e)}") from e
    
    def benchmark_performance(self, num_properties: int = 1000) -> Dict:
        """
        Benchmark system performance with synthetic data
        
        Args:
            num_properties: Number of properties to test with
            
        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Starting performance benchmark with {num_properties} properties")
        
        import numpy as np
        
        # Generate test coordinates around LA
        np.random.seed(42)  # For reproducible results
        test_lats = np.random.normal(34.0522, 0.1, num_properties)
        test_lons = np.random.normal(-118.2437, 0.1, num_properties)
        
        # Create test DataFrame
        test_df = pd.DataFrame({
            'property_id': range(num_properties),
            'latitude': test_lats,
            'longitude': test_lons
        })
        
        start_time = time.time()
        
        try:
            # Process batch
            result_df = self.process_properties_batch(test_df)
            
            processing_time = time.time() - start_time
            properties_per_second = num_properties / processing_time
            
            # Analyze results
            tier_distribution = result_df['toc_toc_tier'].value_counts().sort_index()
            
            benchmark_results = {
                'num_properties_tested': num_properties,
                'total_processing_time_seconds': processing_time,
                'properties_per_second': properties_per_second,
                'average_time_per_property_ms': (processing_time / num_properties) * 1000,
                'tier_distribution': tier_distribution.to_dict(),
                'engine_metrics': self.engine.get_performance_metrics(),
                'timestamp': time.time()
            }
            
            logger.info(f"Benchmark completed: {properties_per_second:.1f} properties/second")
            
            return benchmark_results
            
        except Exception as e:
            logger.error(f"Performance benchmark failed: {str(e)}")
            raise TOCTierEngineError(f"Benchmark failed: {str(e)}") from e


# Convenience functions for backward compatibility
def calculate_toc_tier(property_lat: float, property_lon: float) -> Dict:
    """
    Convenience function for single property calculation
    
    Args:
        property_lat: Property latitude
        property_lon: Property longitude
        
    Returns:
        Dictionary with TOC calculation results
    """
    calculator = TOCTierCalculatorOptimized()
    return calculator.calculate_toc_tier(property_lat, property_lon)


def process_properties_batch(properties_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function for batch processing
    
    Args:
        properties_df: DataFrame with property coordinates
        
    Returns:
        DataFrame with TOC tier results added
    """
    calculator = TOCTierCalculatorOptimized()
    return calculator.process_properties_batch(properties_df)


def validate_toc_system() -> Dict:
    """
    Convenience function for system validation
    
    Returns:
        Dictionary with validation results
    """
    calculator = TOCTierCalculatorOptimized()
    return calculator.validate_system()


def main():
    """Test the optimized TOC calculator"""
    print("🚀 TESTING OPTIMIZED TOC CALCULATOR")
    print("=" * 80)
    
    try:
        # Initialize calculator
        calculator = TOCTierCalculatorOptimized()
        
        # System validation
        print("\n🔍 SYSTEM VALIDATION")
        print("-" * 40)
        validation = calculator.validate_system()
        print(f"Overall Status: {validation['overall_status'].upper()}")
        print(f"Accuracy Rate: {validation['accuracy_rate']*100:.1f}%")
        print(f"Health Status: {validation['health_check']['status']}")
        
        # Performance benchmark
        print("\n⚡ PERFORMANCE BENCHMARK")
        print("-" * 40)
        benchmark = calculator.benchmark_performance(100)
        print(f"Processing Speed: {benchmark['properties_per_second']:.1f} properties/second")
        print(f"Average Time: {benchmark['average_time_per_property_ms']:.2f}ms per property")
        
        # System metrics
        print("\n📊 SYSTEM METRICS")
        print("-" * 40)
        metrics = calculator.get_system_metrics()
        print(f"Total Processed: {metrics['total_properties_processed']} properties")
        print(f"Engine Health: {metrics['system_health']['status']}")
        
        print("\n✅ OPTIMIZED TOC CALCULATOR TEST COMPLETE")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        logger.exception("Test execution failed")


if __name__ == "__main__":
    main()