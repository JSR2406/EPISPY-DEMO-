"""
Similarity matching algorithm for contextual policy recommendations.

This module implements similarity matching between locations based on
demographics, economics, infrastructure, culture, and health system characteristics.
Uses weighted distance metrics and feature normalization for accurate matching.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database.models import Location, LocationContext, Policy, PolicyOutcome
from ..utils.logger import api_logger


@dataclass
class SimilarityWeights:
    """Weights for different similarity dimensions."""
    population_density: float = 0.15
    gdp_per_capita: float = 0.15
    healthcare_capacity: float = 0.20
    urbanization_rate: float = 0.10
    literacy_rate: float = 0.05
    internet_penetration: float = 0.05
    infrastructure_quality: float = 0.10
    governance_effectiveness: float = 0.10
    public_trust_score: float = 0.10
    
    def normalize(self) -> "SimilarityWeights":
        """Normalize weights to sum to 1.0."""
        total = sum([
            self.population_density,
            self.gdp_per_capita,
            self.healthcare_capacity,
            self.urbanization_rate,
            self.literacy_rate,
            self.internet_penetration,
            self.infrastructure_quality,
            self.governance_effectiveness,
            self.public_trust_score,
        ])
        if total == 0:
            return self
        return SimilarityWeights(
            population_density=self.population_density / total,
            gdp_per_capita=self.gdp_per_capita / total,
            healthcare_capacity=self.healthcare_capacity / total,
            urbanization_rate=self.urbanization_rate / total,
            literacy_rate=self.literacy_rate / total,
            internet_penetration=self.internet_penetration / total,
            infrastructure_quality=self.infrastructure_quality / total,
            governance_effectiveness=self.governance_effectiveness / total,
            public_trust_score=self.public_trust_score / total,
        )


@dataclass
class LocationFeatures:
    """Normalized features for a location."""
    population_density: float = 0.0
    gdp_per_capita: float = 0.0
    healthcare_capacity: float = 0.0
    urbanization_rate: float = 0.0
    literacy_rate: float = 0.0
    internet_penetration: float = 0.0
    infrastructure_quality: float = 0.0
    governance_effectiveness: float = 0.0
    public_trust_score: float = 0.0
    
    def to_vector(self) -> np.ndarray:
        """Convert features to numpy array."""
        return np.array([
            self.population_density,
            self.gdp_per_capita,
            self.healthcare_capacity,
            self.urbanization_rate,
            self.literacy_rate,
            self.internet_penetration,
            self.infrastructure_quality,
            self.governance_effectiveness,
            self.public_trust_score,
        ])


class SimilarityMatcher:
    """
    Similarity matcher for finding locations with similar contexts.
    
    Uses weighted distance metrics to find locations similar to a target location
    based on demographic, economic, infrastructure, and cultural factors.
    
    Example:
        matcher = SimilarityMatcher(session)
        similar_locations = await matcher.find_similar_locations(
            target_location_id=location_id,
            top_k=10
        )
    """
    
    def __init__(
        self,
        session: AsyncSession,
        weights: Optional[SimilarityWeights] = None
    ):
        """
        Initialize similarity matcher.
        
        Args:
            session: Database session
            weights: Custom similarity weights (default: balanced weights)
        """
        self.session = session
        self.weights = weights.normalize() if weights else SimilarityWeights().normalize()
        self._feature_stats: Optional[Dict[str, Dict[str, float]]] = None
    
    async def _compute_feature_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Compute normalization statistics for all features.
        
        Returns:
            Dictionary with min/max/mean/std for each feature
        """
        if self._feature_stats is not None:
            return self._feature_stats
        
        # Fetch all location contexts
        result = await self.session.execute(
            select(LocationContext)
        )
        contexts = result.scalars().all()
        
        if not contexts:
            # Return default stats if no data
            self._feature_stats = {
                "population_density": {"min": 0, "max": 1, "mean": 0, "std": 1},
                "gdp_per_capita": {"min": 0, "max": 1, "mean": 0, "std": 1},
                "healthcare_capacity": {"min": 0, "max": 10, "mean": 5, "std": 2},
                "urbanization_rate": {"min": 0, "max": 100, "mean": 50, "std": 20},
                "literacy_rate": {"min": 0, "max": 100, "mean": 80, "std": 15},
                "internet_penetration": {"min": 0, "max": 100, "mean": 60, "std": 25},
                "infrastructure_quality": {"min": 0, "max": 10, "mean": 5, "std": 2},
                "governance_effectiveness": {"min": 0, "max": 10, "mean": 5, "std": 2},
                "public_trust_score": {"min": 0, "max": 10, "mean": 5, "std": 2},
            }
            return self._feature_stats
        
        # Extract feature values
        features = {
            "population_density": [],
            "gdp_per_capita": [],
            "healthcare_capacity": [],
            "urbanization_rate": [],
            "literacy_rate": [],
            "internet_penetration": [],
            "infrastructure_quality": [],
            "governance_effectiveness": [],
            "public_trust_score": [],
        }
        
        for context in contexts:
            if context.population_density is not None:
                features["population_density"].append(context.population_density)
            if context.gdp_per_capita is not None:
                features["gdp_per_capita"].append(context.gdp_per_capita)
            if context.healthcare_capacity is not None:
                features["healthcare_capacity"].append(context.healthcare_capacity)
            if context.urbanization_rate is not None:
                features["urbanization_rate"].append(context.urbanization_rate)
            if context.literacy_rate is not None:
                features["literacy_rate"].append(context.literacy_rate)
            if context.internet_penetration is not None:
                features["internet_penetration"].append(context.internet_penetration)
            if context.infrastructure_quality is not None:
                features["infrastructure_quality"].append(context.infrastructure_quality)
            if context.governance_effectiveness is not None:
                features["governance_effectiveness"].append(context.governance_effectiveness)
            if context.public_trust_score is not None:
                features["public_trust_score"].append(context.public_trust_score)
        
        # Compute statistics
        stats = {}
        for feature_name, values in features.items():
            if values:
                stats[feature_name] = {
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)) if len(values) > 1 else 1.0,
                }
            else:
                # Default stats if no data
                stats[feature_name] = {"min": 0, "max": 1, "mean": 0, "std": 1}
        
        self._feature_stats = stats
        return stats
    
    def _extract_features(self, context: Optional[LocationContext]) -> LocationFeatures:
        """
        Extract and normalize features from location context.
        
        Args:
            context: LocationContext object
            
        Returns:
            LocationFeatures with normalized values
        """
        stats = self._feature_stats or {}
        
        def normalize(value: Optional[float], feature_name: str) -> float:
            """Normalize a feature value to [0, 1] range."""
            if value is None:
                return 0.0
            
            feature_stats = stats.get(feature_name, {"min": 0, "max": 1})
            min_val = feature_stats["min"]
            max_val = feature_stats["max"]
            
            if max_val == min_val:
                return 0.5  # Default to middle if no range
            
            normalized = (value - min_val) / (max_val - min_val)
            return max(0.0, min(1.0, normalized))  # Clamp to [0, 1]
        
        if context is None:
            return LocationFeatures()
        
        return LocationFeatures(
            population_density=normalize(context.population_density, "population_density"),
            gdp_per_capita=normalize(context.gdp_per_capita, "gdp_per_capita"),
            healthcare_capacity=normalize(context.healthcare_capacity, "healthcare_capacity"),
            urbanization_rate=normalize(context.urbanization_rate, "urbanization_rate"),
            literacy_rate=normalize(context.literacy_rate, "literacy_rate"),
            internet_penetration=normalize(context.internet_penetration, "internet_penetration"),
            infrastructure_quality=normalize(context.infrastructure_quality, "infrastructure_quality"),
            governance_effectiveness=normalize(context.governance_effectiveness, "governance_effectiveness"),
            public_trust_score=normalize(context.public_trust_score, "public_trust_score"),
        )
    
    def _compute_similarity(
        self,
        features1: LocationFeatures,
        features2: LocationFeatures
    ) -> float:
        """
        Compute weighted cosine similarity between two location feature vectors.
        
        Args:
            features1: Features of first location
            features2: Features of second location
            
        Returns:
            Similarity score between 0 and 1 (1 = identical, 0 = completely different)
        """
        vec1 = features1.to_vector()
        vec2 = features2.to_vector()
        weights = np.array([
            self.weights.population_density,
            self.weights.gdp_per_capita,
            self.weights.healthcare_capacity,
            self.weights.urbanization_rate,
            self.weights.literacy_rate,
            self.weights.internet_penetration,
            self.weights.infrastructure_quality,
            self.weights.governance_effectiveness,
            self.weights.public_trust_score,
        ])
        
        # Weighted cosine similarity
        weighted_vec1 = vec1 * weights
        weighted_vec2 = vec2 * weights
        
        dot_product = np.dot(weighted_vec1, weighted_vec2)
        norm1 = np.linalg.norm(weighted_vec1)
        norm2 = np.linalg.norm(weighted_vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Also compute weighted Euclidean distance for additional context
        # Convert distance to similarity (inverse relationship)
        distance = np.sqrt(np.sum(weights * (vec1 - vec2) ** 2))
        distance_similarity = 1.0 / (1.0 + distance)
        
        # Combine both metrics (weighted average)
        combined_similarity = 0.7 * similarity + 0.3 * distance_similarity
        
        return float(np.clip(combined_similarity, 0.0, 1.0))
    
    async def find_similar_locations(
        self,
        target_location_id: str,
        top_k: int = 10,
        min_similarity: float = 0.5
    ) -> List[Tuple[Location, float]]:
        """
        Find locations similar to target location.
        
        Args:
            target_location_id: UUID of target location
            top_k: Number of similar locations to return
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of tuples (Location, similarity_score) sorted by similarity
        """
        # Compute feature statistics
        await self._compute_feature_stats()
        
        # Get target location context
        result = await self.session.execute(
            select(LocationContext)
            .where(LocationContext.location_id == target_location_id)
        )
        target_context = result.scalar_one_or_none()
        target_features = self._extract_features(target_context)
        
        # Get all other location contexts
        result = await self.session.execute(
            select(LocationContext)
            .where(LocationContext.location_id != target_location_id)
            .options(selectinload(LocationContext.location))
        )
        all_contexts = result.scalars().all()
        
        # Compute similarities
        similarities = []
        for context in all_contexts:
            features = self._extract_features(context)
            similarity = self._compute_similarity(target_features, features)
            
            if similarity >= min_similarity:
                similarities.append((context.location, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return similarities[:top_k]
    
    async def compute_similarity_matrix(
        self,
        location_ids: List[str]
    ) -> Dict[Tuple[str, str], float]:
        """
        Compute similarity matrix for a set of locations.
        
        Args:
            location_ids: List of location UUIDs
            
        Returns:
            Dictionary mapping (location_id1, location_id2) -> similarity_score
        """
        await self._compute_feature_stats()
        
        # Fetch all contexts
        result = await self.session.execute(
            select(LocationContext)
            .where(LocationContext.location_id.in_(location_ids))
        )
        contexts = {str(ctx.location_id): ctx for ctx in result.scalars().all()}
        
        # Compute pairwise similarities
        similarity_matrix = {}
        location_list = list(location_ids)
        
        for i, loc_id1 in enumerate(location_list):
            features1 = self._extract_features(contexts.get(loc_id1))
            for loc_id2 in location_list[i+1:]:
                features2 = self._extract_features(contexts.get(loc_id2))
                similarity = self._compute_similarity(features1, features2)
                similarity_matrix[(loc_id1, loc_id2)] = similarity
                similarity_matrix[(loc_id2, loc_id1)] = similarity  # Symmetric
        
        return similarity_matrix

