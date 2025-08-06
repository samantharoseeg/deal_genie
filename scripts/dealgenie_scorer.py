#!/usr/bin/env python3
"""
DealGenie Property Scoring Engine

A comprehensive property scoring system for real estate development potential analysis.
Provides multi-factor scoring, investment tier classification, and development use case recommendations.

Security Features:
- Input validation and sanitization
- Safe file path handling
- Configuration validation
- Protected against code injection

Author: DealGenie Team
Version: 2.0.0
License: MIT
"""

import pandas as pd
import numpy as np
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Union
from dataclasses import dataclass
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


@dataclass
class ScoringResult:
    """Data class for scoring results with type safety"""
    total_score: float
    component_scores: Dict[str, float]
    investment_tier: str
    suggested_use: str
    
    def __post_init__(self):
        """Validate scoring result data"""
        if not (0 <= self.total_score <= 100):
            raise ValueError(f"Total score must be between 0-100, got {self.total_score}")
        if self.investment_tier not in ['A', 'B', 'C', 'D']:
            raise ValueError(f"Invalid investment tier: {self.investment_tier}")


class ConfigurationError(Exception):
    """Raised when configuration is invalid or corrupted"""
    pass


class DataValidationError(Exception):
    """Raised when input data fails validation"""
    pass


class DealGenieScorer:
    """
    Comprehensive property scoring engine for development potential analysis.
    
    This class provides a secure, robust scoring system that evaluates real estate
    properties based on multiple factors including zoning, lot size, transit access,
    financial metrics, and risk factors.
    
    Security considerations:
    - All file paths are validated and sanitized
    - Configuration is validated against schema
    - Input data is sanitized and validated
    - Protected against injection attacks
    """
    
    # Class constants for validation
    VALID_ZONING_PREFIXES = {'R', 'C', 'M', 'PF', 'OS', 'A', 'RAS', 'RD', 'CM', 'MR'}
    VALID_INVESTMENT_TIERS = {'A', 'B', 'C', 'D'}
    MAX_LOT_SIZE_SQFT = 10_000_000  # 10M sqft sanity check
    MAX_BUILDING_SIZE_SQFT = 5_000_000  # 5M sqft sanity check
    MAX_ASSESSED_VALUE = 1_000_000_000  # $1B sanity check
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize scorer with validated configuration.
        
        Args:
            config_path: Optional path to JSON configuration file
            
        Raises:
            ConfigurationError: If configuration is invalid
            FileNotFoundError: If config file doesn't exist
            PermissionError: If config file can't be read
        """
        self.config_path = None
        
        try:
            if config_path:
                self.config_path = self._validate_config_path(config_path)
                self.config = self._load_config_file(self.config_path)
            else:
                self.config = self._get_default_config()
            
            self._validate_configuration()
            logger.info("DealGenieScorer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scorer: {e}")
            raise ConfigurationError(f"Initialization failed: {e}") from e
    
    def _validate_config_path(self, config_path: str) -> Path:
        """
        Validate and sanitize configuration file path.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Validated Path object
            
        Raises:
            ValueError: If path is invalid or unsafe
        """
        if not isinstance(config_path, (str, Path)):
            raise ValueError("Config path must be string or Path object")
        
        path = Path(config_path).resolve()
        
        # Security: Prevent directory traversal attacks
        if '..' in str(path) or str(path).startswith('/'):
            raise ValueError("Unsafe config path detected")
        
        # Validate file extension
        if path.suffix.lower() != '.json':
            raise ValueError("Config file must have .json extension")
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Config path is not a file: {path}")
        
        return path
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """
        Safely load configuration from JSON file.
        
        Args:
            config_path: Validated path to config file
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If file can't be loaded or parsed
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not isinstance(config, dict):
                raise ValueError("Config file must contain a JSON object")
            
            logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file: {e}") from e
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default scoring configuration with validation.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "weights": {
                "zoning_score": 0.35,
                "lot_size_score": 0.25,
                "transit_bonus": 0.20,
                "financial_score": 0.10,
                "risk_penalty": 0.10
            },
            "zoning_scores": {
                # High density residential
                "R5": 100, "RAS4": 95, "RAS3": 92, "R4": 90,
                # Medium-high density
                "RD3": 85, "RD2.5": 82, "RD2": 80, "R3": 75, "RD1.5": 72, "RD1": 70,
                # Commercial zones
                "C4": 95, "C2": 90, "CM": 85, "C1.5": 82, "C1": 80,
                # Industrial (light)
                "M2": 75, "M1": 70, "MR1": 72, "MR2": 74,
                # Low density residential
                "R2": 50, "RD5": 48, "RD4": 45, "RD6": 43,
                "R1": 40, "RS": 38, "RE": 35, "RA": 32,
                # Special zones
                "PF": 25, "OS": 20, "A1": 15, "A2": 15
            },
            "lot_size_thresholds": [
                {"min": 20000, "max": float('inf'), "score_range": [90, 100]},
                {"min": 10000, "max": 20000, "score_range": [80, 90]},
                {"min": 7000, "max": 10000, "score_range": [70, 80]},
                {"min": 5000, "max": 7000, "score_range": [60, 70]},
                {"min": 3000, "max": 5000, "score_range": [40, 60]},
                {"min": 0, "max": 3000, "score_range": [20, 40]}
            ],
            "transit_bonuses": {
                "toc_eligible": 20,
                "high_quality_transit": 15,
                "opportunity_corridor": 10,
                "tier_1": 25,
                "tier_2": 20,
                "tier_3": 15,
                "tier_4": 10
            },
            "financial_bonuses": {
                "high_land_ratio": {"threshold": 0.70, "bonus": 10},
                "low_far": {"threshold": 0.50, "bonus": 5},
                "very_low_far": {"threshold": 0.25, "bonus": 8}
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
                "A": {"min": 80, "description": "Prime Development Opportunity"},
                "B": {"min": 65, "description": "Strong Development Potential"},
                "C": {"min": 50, "description": "Moderate Development Potential"},
                "D": {"min": 0, "description": "Limited Development Potential"}
            }
        }
    
    def _validate_configuration(self) -> None:
        """
        Validate configuration structure and values.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        required_sections = [
            'weights', 'zoning_scores', 'lot_size_thresholds',
            'transit_bonuses', 'financial_bonuses', 'risk_penalties', 'investment_tiers'
        ]
        
        # Check required sections exist
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required config section: {section}")
        
        # Validate weights sum to approximately 1.0
        weights = self.config.get('weights', {})
        weight_sum = sum(weights.values())
        if not (0.95 <= weight_sum <= 1.05):
            raise ConfigurationError(f"Weights must sum to ~1.0, got {weight_sum}")
        
        # Validate weight values are reasonable
        for weight_name, weight_value in weights.items():
            if not (0 <= weight_value <= 1):
                raise ConfigurationError(f"Weight {weight_name} must be 0-1, got {weight_value}")
        
        # Validate zoning scores
        zoning_scores = self.config.get('zoning_scores', {})
        for zone, score in zoning_scores.items():
            if not isinstance(zone, str) or not zone.strip():
                raise ConfigurationError(f"Invalid zoning code: {zone}")
            if not (0 <= score <= 100):
                raise ConfigurationError(f"Zoning score for {zone} must be 0-100, got {score}")
        
        # Validate investment tiers
        tiers = self.config.get('investment_tiers', {})
        for tier in self.VALID_INVESTMENT_TIERS:
            if tier not in tiers:
                raise ConfigurationError(f"Missing investment tier: {tier}")
            if 'min' not in tiers[tier]:
                raise ConfigurationError(f"Investment tier {tier} missing 'min' value")
        
        logger.info("Configuration validation successful")
    
    def _sanitize_string_input(self, value: Any) -> str:
        """
        Safely convert and sanitize string input.
        
        Args:
            value: Input value to sanitize
            
        Returns:
            Sanitized string
        """
        if pd.isna(value):
            return ""
        
        # Convert to string and strip whitespace
        sanitized = str(value).strip()
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '`', '|', ';']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.upper()
    
    def _validate_numeric_input(self, value: Any, min_val: float = 0, 
                              max_val: float = float('inf'), 
                              field_name: str = "value") -> float:
        """
        Validate and sanitize numeric input with bounds checking.
        
        Args:
            value: Input value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value  
            field_name: Name of field for error messages
            
        Returns:
            Validated numeric value
            
        Raises:
            ValueError: If value is invalid or out of bounds
        """
        if pd.isna(value):
            return 0.0
        
        try:
            num_value = float(value)
            
            # Check for infinite or NaN values
            if not np.isfinite(num_value):
                logger.warning(f"Invalid numeric value for {field_name}: {value}")
                return 0.0
            
            # Bounds checking
            if not (min_val <= num_value <= max_val):
                logger.warning(f"{field_name} value {num_value} outside bounds [{min_val}, {max_val}]")
                return max(min_val, min(max_val, num_value))
            
            return num_value
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not convert {field_name} to numeric: {value}, error: {e}")
            return 0.0
    
    def calculate_zoning_score(self, base_zoning: Any) -> float:
        """
        Calculate zoning score with enhanced validation and security.
        
        Args:
            base_zoning: Raw zoning code input
            
        Returns:
            Zoning score (0-100)
        """
        try:
            if pd.isna(base_zoning):
                return 30.0
            
            # Sanitize zoning input
            zoning_code = self._sanitize_string_input(base_zoning)
            
            if not zoning_code:
                return 30.0
            
            # Validate zoning code format
            if len(zoning_code) > 10:  # Reasonable limit
                logger.warning(f"Unusually long zoning code: {zoning_code}")
                zoning_code = zoning_code[:10]
            
            # Check if zoning starts with valid prefix
            valid_prefix = any(zoning_code.startswith(prefix) for prefix in self.VALID_ZONING_PREFIXES)
            if not valid_prefix:
                logger.warning(f"Unknown zoning prefix: {zoning_code}")
            
            # Direct lookup
            zoning_scores = self.config.get("zoning_scores", {})
            if zoning_code in zoning_scores:
                score = zoning_scores[zoning_code]
                return self._validate_numeric_input(score, 0, 100, "zoning_score")
            
            # Pattern matching with safety limit
            for zone_pattern, score in zoning_scores.items():
                if zoning_code.startswith(zone_pattern):
                    return self._validate_numeric_input(score, 0, 100, "zoning_score")
            
            # Default for unknown zones
            logger.info(f"Unknown zoning code, using default: {zoning_code}")
            return 35.0
            
        except Exception as e:
            logger.error(f"Error calculating zoning score for {base_zoning}: {e}")
            return 30.0  # Safe default
    
    def calculate_lot_size_score(self, lot_size_sqft: Any) -> float:
        """
        Calculate lot size score with comprehensive validation.
        
        Args:
            lot_size_sqft: Raw lot size input
            
        Returns:
            Lot size score (0-100)
        """
        try:
            validated_size = self._validate_numeric_input(
                lot_size_sqft, 0, self.MAX_LOT_SIZE_SQFT, "lot_size"
            )
            
            if validated_size <= 0:
                return 20.0
            
            # Process thresholds with safety checks
            thresholds = self.config.get("lot_size_thresholds", [])
            if not thresholds:
                logger.error("No lot size thresholds configured")
                return 30.0
            
            for threshold in thresholds:
                if not isinstance(threshold, dict):
                    continue
                
                min_size = threshold.get("min", 0)
                max_size = threshold.get("max", float('inf'))
                score_range = threshold.get("score_range", [20, 40])
                
                if len(score_range) != 2:
                    continue
                
                if min_size <= validated_size < max_size:
                    score_min, score_max = score_range
                    
                    # Handle infinite upper bound
                    if max_size == float('inf'):
                        return min(100, score_max)
                    
                    # Linear interpolation with division by zero protection
                    range_size = max_size - min_size
                    if range_size <= 0:
                        return score_min
                    
                    position = (validated_size - min_size) / range_size
                    score = score_min + (score_max - score_min) * position
                    
                    return max(0, min(100, score))
            
            return 30.0
            
        except Exception as e:
            logger.error(f"Error calculating lot size score for {lot_size_sqft}: {e}")
            return 20.0  # Safe default
    
    def calculate_transit_bonus(self, row: pd.Series) -> float:
        """
        Calculate transit bonuses with enhanced validation.
        
        Args:
            row: Property data row
            
        Returns:
            Transit bonus score (0-40, capped)
        """
        try:
            bonus = 0.0
            bonuses = self.config.get("transit_bonuses", {})
            
            # TOC eligibility with type checking
            toc_eligible = row.get('toc_eligible', False)
            if isinstance(toc_eligible, (bool, np.bool_)) and toc_eligible:
                bonus += bonuses.get("toc_eligible", 0)
            elif isinstance(toc_eligible, str) and toc_eligible.lower() == 'true':
                bonus += bonuses.get("toc_eligible", 0)
            
            # High quality transit
            transit_quality = self._sanitize_string_input(row.get('high_quality_transit', ''))
            if transit_quality == 'YES':
                bonus += bonuses.get("high_quality_transit", 0)
            
            # Opportunity zones with enhanced parsing
            opp_zone = self._sanitize_string_input(row.get('opportunity_zone', ''))
            if opp_zone and opp_zone not in ['NOT ELIGIBLE', 'NONE', '']:
                if 'OC-1' in opp_zone or 'TIER 1' in opp_zone:
                    bonus += bonuses.get("tier_1", 0)
                elif 'OC-2' in opp_zone or 'TIER 2' in opp_zone:
                    bonus += bonuses.get("tier_2", 0)
                elif 'OC-3' in opp_zone or 'TIER 3' in opp_zone:
                    bonus += bonuses.get("tier_3", 0)
                elif 'OC-4' in opp_zone or 'TIER 4' in opp_zone:
                    bonus += bonuses.get("tier_4", 0)
                else:
                    bonus += bonuses.get("opportunity_corridor", 0)
            
            # Cap bonus to prevent score inflation
            return min(bonus, 40.0)
            
        except Exception as e:
            logger.error(f"Error calculating transit bonus: {e}")
            return 0.0  # Safe default
    
    def calculate_financial_score(self, row: pd.Series) -> float:
        """
        Calculate financial indicators with enhanced validation and error handling.
        
        Args:
            row: Property data row
            
        Returns:
            Financial score (0-15, capped)
        """
        try:
            score = 0.0
            bonuses = self.config.get("financial_bonuses", {})
            
            # Land value ratio calculation with safety checks
            land_value = self._validate_numeric_input(
                row.get('assessed_land_value', 0), 0, self.MAX_ASSESSED_VALUE, "land_value"
            )
            total_value = self._validate_numeric_input(
                row.get('total_assessed_value', 0), 0, self.MAX_ASSESSED_VALUE, "total_value"
            )
            
            if total_value > 0 and land_value > 0:
                land_ratio = land_value / total_value
                
                # Sanity check: land ratio shouldn't exceed 100%
                if land_ratio <= 1.0:
                    high_ratio_config = bonuses.get("high_land_ratio", {})
                    threshold = high_ratio_config.get("threshold", 0.70)
                    
                    if land_ratio >= threshold:
                        score += high_ratio_config.get("bonus", 0)
            
            # FAR (Floor Area Ratio) calculation with safety checks
            building_size = self._validate_numeric_input(
                row.get('building_size_sqft', 0), 0, self.MAX_BUILDING_SIZE_SQFT, "building_size"
            )
            lot_size = self._validate_numeric_input(
                row.get('lot_size_sqft', 0), 1, self.MAX_LOT_SIZE_SQFT, "lot_size"  # min=1 to avoid division by zero
            )
            
            if lot_size > 0 and building_size > 0:
                far = building_size / lot_size
                
                # Sanity check: FAR shouldn't be extremely high
                if far <= 10.0:  # Reasonable upper limit
                    very_low_config = bonuses.get("very_low_far", {})
                    low_config = bonuses.get("low_far", {})
                    
                    if far <= very_low_config.get("threshold", 0.25):
                        score += very_low_config.get("bonus", 0)
                    elif far <= low_config.get("threshold", 0.50):
                        score += low_config.get("bonus", 0)
            
            # Cap score to prevent inflation
            return min(score, 15.0)
            
        except Exception as e:
            logger.error(f"Error calculating financial score: {e}")
            return 0.0  # Safe default
    
    def calculate_risk_penalty(self, row: pd.Series) -> float:
        """
        Calculate risk penalties with comprehensive validation.
        
        Args:
            row: Property data row
            
        Returns:
            Risk penalty score (0-20, capped)
        """
        try:
            penalty = 0.0
            penalties = self.config.get("risk_penalties", {})
            
            # Overlay zones with bounds checking
            overlay_count = self._validate_numeric_input(
                row.get('overlay_count', 0), 0, 20, "overlay_count"  # Max 20 overlays is reasonable
            )
            penalty += overlay_count * penalties.get("overlay_per_zone", 0)
            
            # Environmental hazards
            methane = self._sanitize_string_input(row.get('methane_zone', ''))
            if 'METHANE ZONE' in methane:
                penalty += penalties.get("methane_zone", 0)
            elif 'BUFFER' in methane:
                penalty += penalties.get("methane_buffer", 0)
            
            # Historic preservation
            specific_plan = self._sanitize_string_input(row.get('specific_plan_area', ''))
            if specific_plan and ('HISTORIC' in specific_plan or 'HPOZ' in specific_plan):
                penalty += penalties.get("historic_zone", 0)
            
            # Fault zones
            fault_zone = self._sanitize_string_input(row.get('fault_zone', ''))
            if fault_zone and fault_zone not in ['NONE', '']:
                penalty += penalties.get("fault_zone", 0)
            
            # Flood zones
            flood_zone = self._sanitize_string_input(row.get('flood_zone', ''))
            if 'FLOOD' in flood_zone and 'OUTSIDE' not in flood_zone:
                penalty += penalties.get("flood_zone", 0)
            
            # Fire hazard zones
            fire_zone = self._sanitize_string_input(row.get('very_high_fire_hazard_severity_zone', ''))
            if 'YES' in fire_zone or 'HIGH' in fire_zone:
                penalty += penalties.get("very_high_fire", 0)
            
            # Cap penalty to prevent excessive negative scoring
            return min(penalty, 20.0)
            
        except Exception as e:
            logger.error(f"Error calculating risk penalty: {e}")
            return 0.0  # Safe default (no penalty)
    
    def suggest_use_case(self, row: pd.Series, total_score: float) -> str:
        """
        Suggest development use case with enhanced logic and validation.
        
        Args:
            row: Property data row
            total_score: Calculated development score
            
        Returns:
            Suggested use case string
        """
        try:
            base_zoning = self._sanitize_string_input(row.get('base_zoning', ''))
            lot_size = self._validate_numeric_input(
                row.get('lot_size_sqft', 0), 0, self.MAX_LOT_SIZE_SQFT, "lot_size"
            )
            toc = row.get('toc_eligible', False)
            
            # Calculate land ratio safely
            land_ratio = 0.0
            land_value = self._validate_numeric_input(row.get('assessed_land_value', 0))
            total_value = self._validate_numeric_input(row.get('total_assessed_value', 0))
            
            if total_value > 0 and land_value > 0:
                land_ratio = min(1.0, land_value / total_value)  # Cap at 100%
            
            # Large lot opportunities (10,000+ sqft)
            if lot_size >= 10000:
                if base_zoning.startswith(('R3', 'R4', 'R5', 'RAS')):
                    return "Major TOC Development (100+ units)" if toc else "Large Multi-Family Development"
                elif base_zoning.startswith(('C2', 'C4', 'CM')):
                    return "Mixed-Use Development"
                elif base_zoning.startswith(('M1', 'M2')):
                    return "Creative Office/Live-Work"
                elif land_ratio > 0.7:
                    return "Prime Redevelopment Site"
            
            # Medium lots (5,000-10,000 sqft)
            elif lot_size >= 5000:
                if base_zoning.startswith(('R3', 'R4', 'RD2', 'RD3')):
                    return "TOC Multi-Family (20-50 units)" if toc else "Small Multi-Family Development"
                elif base_zoning.startswith(('C2', 'C4')):
                    return "Retail/Restaurant Development"
                elif base_zoning.startswith(('R1', 'R2')) and land_ratio > 0.65:
                    return "SB9 Lot Split Opportunity"
            
            # Small lots (3,000-5,000 sqft)
            elif lot_size >= 3000:
                if base_zoning.startswith(('R3', 'RD1', 'RD2')):
                    return "Small Lot Subdivision"
                elif base_zoning.startswith(('C1', 'C2')):
                    return "Boutique Retail/Office"
                elif base_zoning.startswith('R1') and toc:
                    return "ADU Development"
            
            # Fallback logic based on zoning and scoring
            if base_zoning.startswith(('C2', 'C4', 'CM')):
                return "Commercial Development"
            elif base_zoning.startswith(('R3', 'R4', 'R5')) and toc:
                return "Transit-Oriented Housing"
            elif land_ratio > 0.75:
                return "Teardown/Rebuild Opportunity"
            elif total_score >= 70:
                return "Development Opportunity"
            elif total_score >= 50:
                return "Value-Add Renovation"
            
            return "Hold/Income Property"
            
        except Exception as e:
            logger.error(f"Error suggesting use case: {e}")
            return "Property Assessment Required"  # Safe fallback
    
    def calculate_property_score(self, row: pd.Series) -> Tuple[float, Dict[str, float]]:
        """
        Calculate comprehensive property development score with full validation.
        
        Args:
            row: Property data row
            
        Returns:
            Tuple of (total_score, component_scores)
            
        Raises:
            DataValidationError: If row data is severely corrupted
        """
        try:
            if not isinstance(row, pd.Series):
                raise DataValidationError("Input must be pandas Series")
            
            weights = self.config.get("weights", {})
            
            # Calculate component scores with error handling
            component_scores = {}
            
            try:
                component_scores["zoning_score"] = self.calculate_zoning_score(row.get('base_zoning'))
            except Exception as e:
                logger.error(f"Zoning score calculation failed: {e}")
                component_scores["zoning_score"] = 30.0
            
            try:
                component_scores["lot_size_score"] = self.calculate_lot_size_score(row.get('lot_size_sqft'))
            except Exception as e:
                logger.error(f"Lot size score calculation failed: {e}")
                component_scores["lot_size_score"] = 20.0
            
            try:
                component_scores["transit_bonus"] = self.calculate_transit_bonus(row)
            except Exception as e:
                logger.error(f"Transit bonus calculation failed: {e}")
                component_scores["transit_bonus"] = 0.0
            
            try:
                component_scores["financial_score"] = self.calculate_financial_score(row)
            except Exception as e:
                logger.error(f"Financial score calculation failed: {e}")
                component_scores["financial_score"] = 0.0
            
            try:
                component_scores["risk_penalty"] = self.calculate_risk_penalty(row)
            except Exception as e:
                logger.error(f"Risk penalty calculation failed: {e}")
                component_scores["risk_penalty"] = 0.0
            
            # Calculate weighted total with safety checks
            total_score = 0.0
            for component, score in component_scores.items():
                weight = weights.get(component, 0.0)
                
                # Risk penalty is subtracted
                if component == "risk_penalty":
                    total_score -= score * weight
                else:
                    total_score += score * weight
            
            # Normalize and clamp to valid range
            total_score = max(0.0, min(100.0, total_score))
            
            # Validate all component scores are reasonable
            for component, score in component_scores.items():
                if not (0 <= score <= 100):
                    logger.warning(f"Component score {component} out of range: {score}")
                    component_scores[component] = max(0, min(100, score))
            
            return total_score, component_scores
            
        except Exception as e:
            logger.error(f"Critical error in property scoring: {e}")
            # Return minimal safe scoring
            return 0.0, {
                "zoning_score": 0.0,
                "lot_size_score": 0.0,
                "transit_bonus": 0.0,
                "financial_score": 0.0,
                "risk_penalty": 0.0
            }
    
    def get_investment_tier(self, score: float) -> str:
        """
        Determine investment tier with validation.
        
        Args:
            score: Development score (0-100)
            
        Returns:
            Investment tier ('A', 'B', 'C', or 'D')
        """
        try:
            # Validate score input
            validated_score = self._validate_numeric_input(score, 0, 100, "investment_score")
            
            tiers = self.config.get("investment_tiers", {})
            
            # Sort tiers by minimum score descending
            sorted_tiers = sorted(
                tiers.items(), 
                key=lambda x: x[1].get("min", 0), 
                reverse=True
            )
            
            for tier, criteria in sorted_tiers:
                min_score = criteria.get("min", 0)
                if validated_score >= min_score:
                    return tier
            
            return "D"  # Fallback
            
        except Exception as e:
            logger.error(f"Error determining investment tier for score {score}: {e}")
            return "D"  # Safe fallback
    
    def score_properties(self, df: pd.DataFrame, batch_size: int = 1000) -> pd.DataFrame:
        """
        Score all properties with enhanced error handling and memory efficiency.
        
        Args:
            df: DataFrame containing property data
            batch_size: Number of properties to process in each batch
            
        Returns:
            DataFrame with scoring results
            
        Raises:
            DataValidationError: If DataFrame is invalid
        """
        if not isinstance(df, pd.DataFrame):
            raise DataValidationError("Input must be pandas DataFrame")
        
        if df.empty:
            raise DataValidationError("DataFrame cannot be empty")
        
        logger.info(f"Starting to score {len(df)} properties in batches of {batch_size}")
        
        # Initialize result columns
        df = df.copy()  # Avoid modifying original data
        df['development_score'] = 0.0
        df['score_breakdown'] = ''
        df['suggested_use'] = ''
        df['investment_tier'] = 'D'
        
        # Process in batches for memory efficiency
        processed = 0
        errors = 0
        
        for start_idx in range(0, len(df), batch_size):
            end_idx = min(start_idx + batch_size, len(df))
            batch = df.iloc[start_idx:end_idx]
            
            logger.info(f"Processing batch {start_idx//batch_size + 1}: rows {start_idx}-{end_idx-1}")
            
            for idx in batch.index:
                try:
                    row = df.loc[idx]
                    score, breakdown = self.calculate_property_score(row)
                    
                    # Update DataFrame with results
                    df.at[idx, 'development_score'] = round(score, 2)
                    df.at[idx, 'score_breakdown'] = json.dumps(breakdown, default=str)
                    df.at[idx, 'suggested_use'] = self.suggest_use_case(row, score)
                    df.at[idx, 'investment_tier'] = self.get_investment_tier(score)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing property at index {idx}: {e}")
                    errors += 1
                    # Set safe defaults for failed properties
                    df.at[idx, 'development_score'] = 0.0
                    df.at[idx, 'score_breakdown'] = '{"error": "processing_failed"}'
                    df.at[idx, 'suggested_use'] = 'Assessment Required'
                    df.at[idx, 'investment_tier'] = 'D'
            
            # Log progress
            if (processed + errors) % (batch_size * 5) == 0:
                logger.info(f"Progress: {processed + errors}/{len(df)} properties processed")
        
        logger.info(f"Scoring complete: {processed} successful, {errors} errors")
        
        if errors > len(df) * 0.1:  # More than 10% errors
            logger.warning(f"High error rate: {errors}/{len(df)} properties failed processing")
        
        return df
    
    def validate_input_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate input DataFrame and return quality metrics.
        
        Args:
            df: Input DataFrame to validate
            
        Returns:
            Dictionary containing validation results and quality metrics
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "row_count": len(df),
            "column_count": len(df.columns),
            "completeness": {},
            "data_quality_score": 0.0
        }
        
        try:
            # Check critical columns
            critical_columns = ['assessor_parcel_id', 'base_zoning', 'lot_size_sqft']
            missing_critical = [col for col in critical_columns if col not in df.columns]
            
            if missing_critical:
                validation_results["errors"].append(f"Missing critical columns: {missing_critical}")
                validation_results["is_valid"] = False
            
            # Calculate completeness for each column
            for col in df.columns:
                if col in df:
                    completeness = (df[col].notna().sum() / len(df)) * 100
                    validation_results["completeness"][col] = round(completeness, 1)
            
            # Calculate overall data quality score
            critical_completeness = [
                validation_results["completeness"].get(col, 0) 
                for col in critical_columns if col in validation_results["completeness"]
            ]
            
            if critical_completeness:
                validation_results["data_quality_score"] = round(
                    sum(critical_completeness) / len(critical_completeness), 1
                )
            
            # Check for suspicious data
            if 'lot_size_sqft' in df.columns:
                large_lots = df[df['lot_size_sqft'] > 1_000_000].shape[0]
                if large_lots > 0:
                    validation_results["warnings"].append(
                        f"{large_lots} properties have lot sizes > 1M sqft"
                    )
            
            logger.info(f"Data validation complete. Quality score: {validation_results['data_quality_score']}%")
            
        except Exception as e:
            logger.error(f"Error during data validation: {e}")
            validation_results["errors"].append(f"Validation failed: {str(e)}")
            validation_results["is_valid"] = False
        
        return validation_results


def validate_file_path(file_path: str, must_exist: bool = True) -> Path:
    """
    Validate and sanitize file path with security checks.
    
    Args:
        file_path: Path to validate
        must_exist: Whether file must already exist
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If path is invalid or unsafe
    """
    if not isinstance(file_path, (str, Path)):
        raise ValueError("File path must be string or Path object")
    
    path = Path(file_path).resolve()
    
    # Security: Basic path traversal protection
    if '..' in str(path):
        raise ValueError("Path traversal detected in file path")
    
    # Check existence if required
    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    return path


def main():
    """
    Main execution function with comprehensive error handling and logging.
    """
    logger.info("=" * 100)
    logger.info("DEALGENIE PROPERTY SCORING ENGINE v2.0")
    logger.info("Enhanced with security, validation, and error handling")
    logger.info("=" * 100)
    
    try:
        # Step 1: Load and validate input data
        logger.info("\n1. Loading and validating input data...")
        
        input_file = 'sample_data/clean_zimas_ready_for_scoring.csv'
        
        try:
            validated_path = validate_file_path(input_file, must_exist=True)
            df = pd.read_csv(validated_path)
            logger.info(f"   Loaded {len(df)} properties from {validated_path}")
        except Exception as e:
            logger.error(f"Failed to load input file: {e}")
            # Try alternative paths
            alternative_paths = [
                'clean_zimas_ready_for_scoring.csv',
                '../sample_data/clean_zimas_ready_for_scoring.csv'
            ]
            
            for alt_path in alternative_paths:
                try:
                    validated_path = validate_file_path(alt_path, must_exist=True)
                    df = pd.read_csv(validated_path)
                    logger.info(f"   Loaded {len(df)} properties from {validated_path}")
                    break
                except Exception:
                    continue
            else:
                raise FileNotFoundError("Could not find input data file")
        
        # Step 2: Initialize scorer with configuration validation
        logger.info("\n2. Initializing scoring engine...")
        
        # Try to load custom config, fallback to defaults
        config_file = None
        possible_configs = ['config/scoring_config.json', 'scoring_config.json']
        
        for config_path in possible_configs:
            try:
                validate_file_path(config_path, must_exist=True)
                config_file = config_path
                break
            except (FileNotFoundError, ValueError):
                continue
        
        scorer = DealGenieScorer(config_path=config_file)
        
        if config_file:
            logger.info(f"   ✓ Using configuration from {config_file}")
        else:
            logger.info("   ✓ Using default configuration")
        
        # Step 3: Validate input data
        logger.info("\n3. Validating input data quality...")
        validation_results = scorer.validate_input_data(df)
        
        if not validation_results["is_valid"]:
            logger.error("Data validation failed:")
            for error in validation_results["errors"]:
                logger.error(f"   - {error}")
            raise DataValidationError("Input data validation failed")
        
        logger.info(f"   ✓ Data quality score: {validation_results['data_quality_score']:.1f}%")
        
        if validation_results["warnings"]:
            for warning in validation_results["warnings"]:
                logger.warning(f"   ! {warning}")
        
        # Step 4: Analyze property distribution
        logger.info("\n4. Property Distribution Analysis:")
        logger.info("-" * 50)
        
        if 'base_zoning' in df.columns:
            zoning_dist = df['base_zoning'].value_counts().head(15)
            for zone, count in zoning_dist.items():
                percentage = count / len(df) * 100
                logger.info(f"   {zone}: {count} properties ({percentage:.1f}%)")
        else:
            logger.warning("   No zoning data available for distribution analysis")
        
        # Step 5: Score all properties
        logger.info("\n5. Calculating development scores...")
        df_scored = scorer.score_properties(df, batch_size=500)
        
        # Step 6: Export results with validation
        logger.info("\n6. Exporting results...")
        output_file = 'sample_data/scored_zimas_properties.csv'
        
        try:
            # Ensure output directory exists
            Path(output_file).parent.mkdir(exist_ok=True)
            df_scored.to_csv(output_file, index=False)
            logger.info(f"   ✓ Results exported to {output_file}")
        except Exception as e:
            # Try alternative output location
            alt_output = 'scored_zimas_properties.csv'
            df_scored.to_csv(alt_output, index=False)
            logger.info(f"   ✓ Results exported to {alt_output}")
        
        # Save configuration for reference
        config_output = 'scoring_config_used.json'
        with open(config_output, 'w', encoding='utf-8') as f:
            json.dump(scorer.config, f, indent=2, default=str)
        logger.info(f"   ✓ Configuration saved to {config_output}")
        
        # Step 7: Generate comprehensive analytics
        logger.info("\n7. COMPREHENSIVE ANALYTICS")
        logger.info("=" * 100)
        
        # Score statistics with error handling
        if 'development_score' in df_scored.columns:
            score_stats = df_scored['development_score'].describe()
            logger.info(f"\nSCORING STATISTICS:")
            logger.info(f"   Mean Score: {score_stats['mean']:.1f}")
            logger.info(f"   Median Score: {score_stats['50%']:.1f}")
            logger.info(f"   Standard Deviation: {score_stats['std']:.1f}")
            logger.info(f"   Score Range: {score_stats['min']:.1f} - {score_stats['max']:.1f}")
            
            # Top properties
            logger.info(f"\nTOP 10 HIGHEST SCORING PROPERTIES:")
            logger.info("-" * 80)
            
            top_properties = df_scored.nlargest(10, 'development_score')
            required_cols = ['assessor_parcel_id', 'development_score', 'investment_tier']
            available_cols = [col for col in required_cols if col in df_scored.columns]
            
            for idx, row in top_properties[available_cols].iterrows():
                score = row.get('development_score', 0)
                tier = row.get('investment_tier', 'D')
                apn = row.get('assessor_parcel_id', 'Unknown')
                logger.info(f"   {score:.1f} | Tier {tier} | {apn}")
        
        # Investment tier distribution
        if 'investment_tier' in df_scored.columns:
            logger.info(f"\nINVESTMENT TIER DISTRIBUTION:")
            logger.info("-" * 50)
            tier_dist = df_scored['investment_tier'].value_counts().sort_index()
            
            for tier in ['A', 'B', 'C', 'D']:
                count = tier_dist.get(tier, 0)
                percentage = count / len(df_scored) * 100
                tier_desc = scorer.config["investment_tiers"][tier]["description"]
                logger.info(f"   Tier {tier} ({tier_desc}): {count} ({percentage:.1f}%)")
        
        # Processing summary
        successful_scores = df_scored[df_scored['development_score'] > 0].shape[0]
        success_rate = (successful_scores / len(df_scored)) * 100
        
        logger.info(f"\nPROCESSING SUMMARY:")
        logger.info("-" * 50)
        logger.info(f"   Total Properties: {len(df_scored)}")
        logger.info(f"   Successfully Scored: {successful_scores} ({success_rate:.1f}%)")
        logger.info(f"   Data Quality Score: {validation_results['data_quality_score']:.1f}%")
        
        logger.info("\n" + "=" * 100)
        logger.info("✅ SCORING ENGINE COMPLETE - Enhanced security and reliability!")
        logger.info("=" * 100)
        
        return df_scored
        
    except Exception as e:
        logger.error(f"Fatal error in scoring engine: {e}")
        logger.error("Please check your input data and configuration files")
        raise


if __name__ == "__main__":
    main()