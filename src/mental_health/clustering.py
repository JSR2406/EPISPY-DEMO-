"""
Geospatial clustering for mental health hotspot detection.

This module provides algorithms for detecting clusters of anxiety/depression
in geographic regions using spatial analysis techniques.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

from ..utils.logger import api_logger
from .models import MentalHealthIndicator, MentalHealthSeverity

# Try to import scikit-learn for clustering
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    api_logger.warning("scikit-learn not available, using simplified clustering")


@dataclass
class Hotspot:
    """Detected mental health hotspot."""
    location_id: str
    latitude: float
    longitude: float
    hotspot_score: float
    primary_indicators: List[str]
    affected_population_estimate: int
    severity: MentalHealthSeverity
    detected_date: datetime
    trend: str
    contributing_factors: Dict[str, Any]


def detect_hotspots(
    data_points: List[Dict[str, Any]],
    location_coordinates: Dict[str, Tuple[float, float]],
    min_samples: int = 5,
    eps_km: float = 10.0
) -> List[Hotspot]:
    """
    Detect mental health hotspots using geospatial clustering.
    
    Uses DBSCAN clustering algorithm to identify geographic clusters
    of mental health indicators.
    
    Args:
        data_points: List of data points with location_id and indicators
        location_coordinates: Dictionary mapping location_id to (lat, lon)
        min_samples: Minimum samples to form a cluster
        eps_km: Maximum distance (km) between points in a cluster
        
    Returns:
        List of detected hotspots
    """
    if not data_points:
        return []
    
    # Prepare data for clustering
    coordinates = []
    location_ids = []
    indicators_list = []
    crisis_scores = []
    
    for point in data_points:
        location_id = point.get("location_id")
        if location_id in location_coordinates:
            lat, lon = location_coordinates[location_id]
            coordinates.append([lat, lon])
            location_ids.append(location_id)
            indicators_list.append(point.get("primary_indicators", []))
            crisis_scores.append(point.get("crisis_score", 0.0))
    
    if len(coordinates) < min_samples:
        return []
    
    coordinates = np.array(coordinates)
    
    # Convert eps from km to degrees (approximate)
    # 1 degree latitude ≈ 111 km, longitude varies by latitude
    eps_degrees = eps_km / 111.0
    
    if SKLEARN_AVAILABLE:
        # Use DBSCAN clustering
        dbscan = DBSCAN(eps=eps_degrees, min_samples=min_samples, metric='haversine')
        
        # Scale coordinates for better clustering
        scaler = StandardScaler()
        coords_scaled = scaler.fit_transform(coordinates)
        
        # For haversine distance, we need (lat, lon) in radians
        # Use simple euclidean distance for simplicity
        from sklearn.metrics.pairwise import haversine_distances
        from math import radians
        
        coords_rad = np.radians(coordinates)
        labels = dbscan.fit_predict(coords_rad)
    else:
        # Simple distance-based clustering
        labels = _simple_clustering(coordinates, eps_degrees, min_samples)
    
    # Extract clusters
    unique_labels = set(labels)
    if -1 in unique_labels:
        unique_labels.remove(-1)  # Remove noise points
    
    hotspots = []
    
    for cluster_id in unique_labels:
        cluster_points = [i for i, label in enumerate(labels) if label == cluster_id]
        
        if len(cluster_points) < min_samples:
            continue
        
        # Calculate cluster center
        cluster_coords = coordinates[cluster_points]
        center_lat = np.mean(cluster_coords[:, 0])
        center_lon = np.mean(cluster_coords[:, 1])
        
        # Aggregate indicators and scores
        cluster_indicators = []
        cluster_scores = []
        
        for idx in cluster_points:
            cluster_indicators.extend(indicators_list[idx])
            cluster_scores.append(crisis_scores[idx])
        
        # Calculate hotspot score
        hotspot_score = np.mean(cluster_scores) if cluster_scores else 0.0
        hotspot_score = min(10.0, hotspot_score)
        
        # Determine severity
        if hotspot_score >= 8.0:
            severity = MentalHealthSeverity.CRITICAL
        elif hotspot_score >= 6.0:
            severity = MentalHealthSeverity.SEVERE
        elif hotspot_score >= 4.0:
            severity = MentalHealthSeverity.MODERATE
        else:
            severity = MentalHealthSeverity.MILD
        
        # Get most common indicators
        from collections import Counter
        indicator_counts = Counter(cluster_indicators)
        primary_indicators = [ind for ind, _ in indicator_counts.most_common(3)]
        
        # Find nearest location_id for cluster center
        nearest_location_id = _find_nearest_location(
            center_lat, center_lon, location_coordinates
        )
        
        # Estimate affected population (simplified)
        affected_population = len(cluster_points) * 100  # Rough estimate
        
        hotspot = Hotspot(
            location_id=nearest_location_id,
            latitude=center_lat,
            longitude=center_lon,
            hotspot_score=float(hotspot_score),
            primary_indicators=primary_indicators,
            affected_population_estimate=affected_population,
            severity=severity,
            detected_date=datetime.now(),
            trend="STABLE",  # Would be calculated from historical data
            contributing_factors={
                "cluster_size": len(cluster_points),
                "average_crisis_score": float(np.mean(cluster_scores)),
                "indicator_distribution": dict(indicator_counts)
            }
        )
        
        hotspots.append(hotspot)
    
    return hotspots


def _simple_clustering(
    coordinates: np.ndarray,
    eps: float,
    min_samples: int
) -> np.ndarray:
    """
    Simple distance-based clustering (fallback when sklearn unavailable).
    
    Args:
        coordinates: Array of (lat, lon) coordinates
        eps: Maximum distance for points in same cluster
        min_samples: Minimum samples per cluster
        
    Returns:
        Array of cluster labels (-1 for noise)
    """
    n_points = len(coordinates)
    labels = np.full(n_points, -1)  # -1 means noise
    cluster_id = 0
    
    visited = set()
    
    for i in range(n_points):
        if i in visited:
            continue
        
        visited.add(i)
        
        # Find neighbors
        neighbors = []
        for j in range(n_points):
            if i != j:
                dist = _haversine_distance(
                    coordinates[i][0], coordinates[i][1],
                    coordinates[j][0], coordinates[j][1]
                )
                if dist <= eps:
                    neighbors.append(j)
        
        if len(neighbors) >= min_samples - 1:  # -1 because we include point i
            # Start new cluster
            labels[i] = cluster_id
            cluster = [i] + neighbors
            
            # Expand cluster
            j = 0
            while j < len(cluster):
                point = cluster[j]
                
                if point not in visited:
                    visited.add(point)
                    
                    # Find neighbors of this point
                    point_neighbors = []
                    for k in range(n_points):
                        if k != point:
                            dist = _haversine_distance(
                                coordinates[point][0], coordinates[point][1],
                                coordinates[k][0], coordinates[k][1]
                            )
                            if dist <= eps:
                                point_neighbors.append(k)
                    
                    # Add new neighbors to cluster
                    for neighbor in point_neighbors:
                        if neighbor not in cluster:
                            cluster.append(neighbor)
                        if labels[neighbor] == -1:
                            labels[neighbor] = cluster_id
                
                j += 1
            
            cluster_id += 1
    
    return labels


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate haversine distance between two points in degrees.
    
    Returns distance in degrees (not km).
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Convert back to degrees (approximate)
    return c * 180 / 3.141592653589793


def _find_nearest_location(
    lat: float,
    lon: float,
    location_coordinates: Dict[str, Tuple[float, float]]
) -> str:
    """Find nearest location to given coordinates."""
    min_dist = float('inf')
    nearest_id = None
    
    for loc_id, (loc_lat, loc_lon) in location_coordinates.items():
        dist = _haversine_distance(lat, lon, loc_lat, loc_lon)
        if dist < min_dist:
            min_dist = dist
            nearest_id = loc_id
    
    return nearest_id or list(location_coordinates.keys())[0] if location_coordinates else "unknown"


def calculate_hotspot_trend(
    historical_scores: List[Tuple[datetime, float]]
) -> str:
    """
    Calculate trend direction for hotspot.
    
    Args:
        historical_scores: List of (datetime, score) tuples
        
    Returns:
        Trend: "INCREASING", "DECREASING", or "STABLE"
    """
    if len(historical_scores) < 2:
        return "STABLE"
    
    # Sort by date
    historical_scores.sort(key=lambda x: x[0])
    
    # Calculate trend
    scores = [score for _, score in historical_scores]
    
    # Simple linear trend
    n = len(scores)
    x = np.arange(n)
    
    # Calculate slope
    slope = np.polyfit(x, scores, 1)[0]
    
    # Determine trend
    if slope > 0.5:
        return "INCREASING"
    elif slope < -0.5:
        return "DECREASING"
    else:
        return "STABLE"

