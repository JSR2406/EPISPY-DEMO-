"""
Evidence quality scoring system for policy outcomes.

This module provides scoring and weighting for evidence quality levels,
helping prioritize recommendations based on data reliability.
"""

from typing import Dict
from ..database.models import EvidenceQuality


class EvidenceQualityScorer:
    """
    Evidence quality scorer for policy recommendations.
    
    Converts evidence quality levels to numeric scores for use in
    recommendation algorithms.
    
    Example:
        scorer = EvidenceQualityScorer()
        score = scorer.score_quality(EvidenceQuality.HIGH)
        # Returns: 0.9
    """
    
    # Quality to score mapping
    QUALITY_SCORES: Dict[EvidenceQuality, float] = {
        EvidenceQuality.VERY_HIGH: 1.0,
        EvidenceQuality.HIGH: 0.9,
        EvidenceQuality.MODERATE: 0.7,
        EvidenceQuality.LOW: 0.5,
        EvidenceQuality.VERY_LOW: 0.3,
    }
    
    def score_quality(self, quality: EvidenceQuality) -> float:
        """
        Convert evidence quality to numeric score.
        
        Args:
            quality: EvidenceQuality enum value
            
        Returns:
            Score between 0 and 1 (higher = better evidence)
        """
        return self.QUALITY_SCORES.get(quality, 0.5)
    
    def get_quality_threshold(self, min_score: float) -> EvidenceQuality:
        """
        Get minimum evidence quality for a given score threshold.
        
        Args:
            min_score: Minimum score (0-1)
            
        Returns:
            Minimum EvidenceQuality level
        """
        # Find the lowest quality that meets the threshold
        for quality in [
            EvidenceQuality.VERY_HIGH,
            EvidenceQuality.HIGH,
            EvidenceQuality.MODERATE,
            EvidenceQuality.LOW,
            EvidenceQuality.VERY_LOW,
        ]:
            if self.score_quality(quality) >= min_score:
                return quality
        
        return EvidenceQuality.VERY_LOW
    
    def weight_by_quality(self, base_score: float, quality: EvidenceQuality) -> float:
        """
        Weight a base score by evidence quality.
        
        Args:
            base_score: Base score to weight
            quality: Evidence quality
            
        Returns:
            Weighted score
        """
        quality_score = self.score_quality(quality)
        # Apply quality as a multiplier with diminishing returns
        # High quality evidence boosts score, low quality reduces it
        return base_score * (0.5 + 0.5 * quality_score)

