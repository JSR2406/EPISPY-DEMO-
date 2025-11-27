"""
NLP-based mental health signal detection algorithms.

This module provides algorithms for detecting mental health crisis signals
from text data (counseling notes, hotline transcripts, social media) using
NLP techniques while maintaining privacy.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import re
import json
from collections import Counter
from dataclasses import dataclass
import numpy as np

from ..utils.logger import api_logger

# Try to import NLP libraries (optional dependencies)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


# Mental health crisis keywords with weights
CRISIS_KEYWORDS = {
    "suicide": 10.0,
    "kill myself": 10.0,
    "end my life": 10.0,
    "suicidal": 9.0,
    "self-harm": 9.0,
    "hurt myself": 9.0,
    "crisis": 8.0,
    "emergency": 7.0,
    "can't cope": 7.0,
    "overwhelmed": 6.0,
    "hopeless": 8.0,
    "helpless": 7.0,
    "no way out": 8.0,
    "no point": 7.0,
    "giving up": 7.0
}

# Anxiety indicators
ANXIETY_KEYWORDS = {
    "anxiety": 5.0,
    "anxious": 5.0,
    "panic": 6.0,
    "panic attack": 7.0,
    "worried": 4.0,
    "worry": 4.0,
    "fear": 5.0,
    "afraid": 4.0,
    "nervous": 4.0,
    "stressed": 5.0,
    "overwhelmed": 5.0,
    "racing thoughts": 6.0,
    "can't breathe": 7.0,
    "chest tightness": 6.0
}

# Depression indicators
DEPRESSION_KEYWORDS = {
    "depression": 6.0,
    "depressed": 6.0,
    "sad": 4.0,
    "hopeless": 7.0,
    "helpless": 6.0,
    "worthless": 7.0,
    "no energy": 5.0,
    "tired": 3.0,
    "exhausted": 4.0,
    "can't sleep": 5.0,
    "insomnia": 5.0,
    "no appetite": 5.0,
    "lost interest": 6.0,
    "nothing matters": 7.0,
    "empty": 6.0
}


@dataclass
class MentalHealthSignal:
    """Detected mental health signal."""
    indicator_type: str
    severity: float  # 0-10
    confidence: float  # 0-1
    keywords_found: List[str]
    language_patterns: Dict[str, Any]
    crisis_score: float  # 0-10
    detected_at: datetime


class NLPModelManager:
    """Manager for NLP models used in mental health signal detection."""
    
    def __init__(self):
        self.crisis_classifier = None
        self.sentiment_analyzer = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize NLP models."""
        if not TRANSFORMERS_AVAILABLE:
            api_logger.warning("Transformers library not available, using rule-based detection only")
            return False
        
        try:
            # Initialize crisis detection model
            # Using a general mental health model or fine-tuned model
            model_name = "j-hartmann/emotion-english-distilroberta-base"
            try:
                self.crisis_classifier = pipeline(
                    "text-classification",
                    model=model_name,
                    tokenizer=model_name,
                    return_all_scores=True
                )
            except Exception:
                # Fallback to simpler model
                api_logger.warning("Could not load crisis classifier, using rule-based detection")
                self.crisis_classifier = None
            
            # Initialize sentiment analyzer
            try:
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
            except Exception:
                api_logger.warning("Could not load sentiment analyzer, using TextBlob")
                if TEXTBLOB_AVAILABLE:
                    self.sentiment_analyzer = "textblob"
                else:
                    self.sentiment_analyzer = None
            
            self.initialized = True
            api_logger.info("NLP models initialized successfully")
            return True
            
        except Exception as e:
            api_logger.error(f"Failed to initialize NLP models: {str(e)}")
            self.initialized = False
            return False


# Global NLP manager instance
_nlp_manager = NLPModelManager()


def detect_mental_health_signals(
    text: str,
    context: Optional[Dict[str, Any]] = None
) -> List[MentalHealthSignal]:
    """
    Detect mental health signals from text.
    
    Uses rule-based keyword matching and optionally NLP models
    to detect mental health indicators in text.
    
    Args:
        text: Text to analyze (anonymized)
        context: Optional context information
        
    Returns:
        List of detected mental health signals
    """
    if not text or len(text.strip()) < 10:
        return []
    
    text_lower = text.lower()
    signals = []
    
    # Detect crisis signals
    crisis_score, crisis_keywords = _calculate_crisis_score(text_lower)
    if crisis_score > 3.0:
        signals.append(MentalHealthSignal(
            indicator_type="CRISIS",
            severity=min(10.0, crisis_score),
            confidence=_calculate_confidence(crisis_score, crisis_keywords),
            keywords_found=crisis_keywords,
            language_patterns=_extract_language_patterns(text),
            crisis_score=crisis_score,
            detected_at=datetime.now()
        ))
    
    # Detect anxiety
    anxiety_score, anxiety_keywords = _calculate_anxiety_score(text_lower)
    if anxiety_score > 2.0:
        signals.append(MentalHealthSignal(
            indicator_type="ANXIETY",
            severity=min(10.0, anxiety_score),
            confidence=_calculate_confidence(anxiety_score, anxiety_keywords),
            keywords_found=anxiety_keywords,
            language_patterns=_extract_language_patterns(text),
            crisis_score=anxiety_score * 0.7,  # Anxiety contributes to crisis score
            detected_at=datetime.now()
        ))
    
    # Detect depression
    depression_score, depression_keywords = _calculate_depression_score(text_lower)
    if depression_score > 2.0:
        signals.append(MentalHealthSignal(
            indicator_type="DEPRESSION",
            severity=min(10.0, depression_score),
            confidence=_calculate_confidence(depression_score, depression_keywords),
            keywords_found=depression_keywords,
            language_patterns=_extract_language_patterns(text),
            crisis_score=depression_score * 0.8,  # Depression contributes more to crisis
            detected_at=datetime.now()
        ))
    
    # Use NLP models if available (optional enhancement)
    if _nlp_manager.initialized and _nlp_manager.crisis_classifier:
        nlp_signals = _detect_with_nlp_models(text)
        # Merge NLP signals with rule-based signals
        signals = _merge_signals(signals, nlp_signals)
    
    return signals


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze sentiment of text.
    
    Returns sentiment scores that can indicate mental health issues.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with sentiment scores and analysis
    """
    sentiment_result = {
        "sentiment_score": 0.0,  # -1 (negative) to 1 (positive)
        "negative_score": 0.0,
        "neutral_score": 0.0,
        "positive_score": 0.0,
        "method": "rule-based"
    }
    
    if not text or len(text.strip()) < 10:
        return sentiment_result
    
    # Use NLP models if available
    if _nlp_manager.initialized and _nlp_manager.sentiment_analyzer:
        if isinstance(_nlp_manager.sentiment_analyzer, str) and _nlp_manager.sentiment_analyzer == "textblob":
            # Use TextBlob
            if TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                sentiment_result["sentiment_score"] = polarity
                sentiment_result["method"] = "textblob"
                
                if polarity < -0.5:
                    sentiment_result["negative_score"] = 1.0
                elif polarity > 0.5:
                    sentiment_result["positive_score"] = 1.0
                else:
                    sentiment_result["neutral_score"] = 1.0
        else:
            # Use transformers model
            try:
                result = _nlp_manager.sentiment_analyzer(text)
                if isinstance(result, list) and len(result) > 0:
                    label = result[0].get("label", "").upper()
                    score = result[0].get("score", 0.0)
                    
                    if "NEGATIVE" in label or "NEG" in label:
                        sentiment_result["negative_score"] = score
                        sentiment_result["sentiment_score"] = -score
                    elif "POSITIVE" in label or "POS" in label:
                        sentiment_result["positive_score"] = score
                        sentiment_result["sentiment_score"] = score
                    else:
                        sentiment_result["neutral_score"] = score
                        sentiment_result["sentiment_score"] = 0.0
                    
                    sentiment_result["method"] = "transformer"
            except Exception as e:
                api_logger.warning(f"Sentiment analysis with model failed: {str(e)}")
    
    # Fallback to rule-based sentiment
    if sentiment_result["method"] == "rule-based":
        sentiment_result = _rule_based_sentiment(text)
    
    return sentiment_result


def calculate_crisis_score(
    signals: List[MentalHealthSignal],
    sentiment: Optional[Dict[str, Any]] = None
) -> float:
    """
    Calculate overall crisis score from multiple signals.
    
    Args:
        signals: List of mental health signals
        sentiment: Optional sentiment analysis result
        
    Returns:
        Crisis score (0-10)
    """
    if not signals:
        return 0.0
    
    # Weight different indicators
    crisis_scores = []
    for signal in signals:
        weight = {
            "CRISIS": 1.0,
            "SUICIDAL_IDEATION": 1.0,
            "DEPRESSION": 0.8,
            "ANXIETY": 0.6,
            "STRESS": 0.5,
            "OTHER": 0.3
        }.get(signal.indicator_type, 0.5)
        
        crisis_scores.append(signal.crisis_score * weight)
    
    # Calculate weighted average
    total_score = sum(crisis_scores)
    max_possible = sum(1.0 for s in signals)
    
    crisis_score = (total_score / max_possible) if max_possible > 0 else 0.0
    
    # Adjust based on sentiment
    if sentiment:
        negative_sentiment = sentiment.get("negative_score", 0.0)
        if negative_sentiment > 0.7:
            crisis_score *= 1.2  # Increase crisis score for strong negative sentiment
        crisis_score = min(10.0, crisis_score)
    
    return min(10.0, crisis_score)


def _calculate_crisis_score(text: str) -> Tuple[float, List[str]]:
    """Calculate crisis score from keywords."""
    score = 0.0
    keywords_found = []
    
    for keyword, weight in CRISIS_KEYWORDS.items():
        if keyword in text:
            score += weight
            keywords_found.append(keyword)
    
    # Normalize score (divide by max possible if all keywords present)
    max_score = sum(CRISIS_KEYWORDS.values()) * 0.5  # Threshold
    normalized_score = min(10.0, (score / max_score) * 10.0) if max_score > 0 else 0.0
    
    return normalized_score, keywords_found


def _calculate_anxiety_score(text: str) -> Tuple[float, List[str]]:
    """Calculate anxiety score from keywords."""
    score = 0.0
    keywords_found = []
    
    for keyword, weight in ANXIETY_KEYWORDS.items():
        if keyword in text:
            score += weight
            keywords_found.append(keyword)
    
    max_score = sum(ANXIETY_KEYWORDS.values()) * 0.3
    normalized_score = min(10.0, (score / max_score) * 10.0) if max_score > 0 else 0.0
    
    return normalized_score, list(set(keywords_found))


def _calculate_depression_score(text: str) -> Tuple[float, List[str]]:
    """Calculate depression score from keywords."""
    score = 0.0
    keywords_found = []
    
    for keyword, weight in DEPRESSION_KEYWORDS.items():
        if keyword in text:
            score += weight
            keywords_found.append(keyword)
    
    max_score = sum(DEPRESSION_KEYWORDS.values()) * 0.3
    normalized_score = min(10.0, (score / max_score) * 10.0) if max_score > 0 else 0.0
    
    return normalized_score, list(set(keywords_found))


def _extract_language_patterns(text: str) -> Dict[str, Any]:
    """Extract language patterns that may indicate mental health issues."""
    patterns = {
        "exclamation_count": text.count("!"),
        "question_count": text.count("?"),
        "negative_words": 0,
        "first_person_pronouns": 0,
        "emotional_intensity": 0.0
    }
    
    # Count negative words
    negative_words = ["no", "not", "never", "nothing", "nobody", "nowhere", "can't", "won't", "don't"]
    text_lower = text.lower()
    patterns["negative_words"] = sum(1 for word in negative_words if word in text_lower)
    
    # Count first-person pronouns (indicates self-focused language)
    first_person = ["i", "me", "my", "myself"]
    patterns["first_person_pronouns"] = sum(
        1 for word in first_person if word in text_lower.split()
    )
    
    # Calculate emotional intensity (based on punctuation and caps)
    caps_count = sum(1 for c in text if c.isupper())
    patterns["emotional_intensity"] = (
        (patterns["exclamation_count"] + patterns["question_count"]) * 0.3 +
        (caps_count / len(text)) * 0.7 if text else 0.0
    )
    
    return patterns


def _rule_based_sentiment(text: str) -> Dict[str, Any]:
    """Rule-based sentiment analysis fallback."""
    sentiment_result = {
        "sentiment_score": 0.0,
        "negative_score": 0.0,
        "neutral_score": 1.0,
        "positive_score": 0.0,
        "method": "rule-based"
    }
    
    text_lower = text.lower()
    
    # Simple word counting approach
    positive_words = ["good", "great", "happy", "better", "improve", "hope", "help", "support"]
    negative_words = ["bad", "terrible", "awful", "horrible", "worse", "hopeless", "helpless", "fear"]
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total = positive_count + negative_count
    if total > 0:
        sentiment_result["positive_score"] = positive_count / total
        sentiment_result["negative_score"] = negative_count / total
        sentiment_result["sentiment_score"] = (positive_count - negative_count) / total
        sentiment_result["neutral_score"] = 1.0 - (sentiment_result["positive_score"] + sentiment_result["negative_score"])
    
    return sentiment_result


def _detect_with_nlp_models(text: str) -> List[MentalHealthSignal]:
    """Detect signals using NLP models (if available)."""
    signals = []
    
    if not _nlp_manager.crisis_classifier:
        return signals
    
    try:
        # Classify text with crisis model
        results = _nlp_manager.crisis_classifier(text, truncation=True, max_length=512)
        
        # Extract relevant classifications
        for result in results[0] if isinstance(results[0], list) else [results]:
            label = result.get("label", "").upper()
            score = result.get("score", 0.0)
            
            # Map to mental health indicators
            if "FEAR" in label or "ANXIETY" in label:
                if score > 0.5:
                    signals.append(MentalHealthSignal(
                        indicator_type="ANXIETY",
                        severity=score * 10,
                        confidence=score,
                        keywords_found=[],
                        language_patterns={},
                        crisis_score=score * 5,
                        detected_at=datetime.now()
                    ))
            elif "SAD" in label or "DEPRESSION" in label:
                if score > 0.5:
                    signals.append(MentalHealthSignal(
                        indicator_type="DEPRESSION",
                        severity=score * 10,
                        confidence=score,
                        keywords_found=[],
                        language_patterns={},
                        crisis_score=score * 7,
                        detected_at=datetime.now()
                    ))
    except Exception as e:
        api_logger.warning(f"NLP model detection failed: {str(e)}")
    
    return signals


def _merge_signals(
    rule_based: List[MentalHealthSignal],
    nlp_based: List[MentalHealthSignal]
) -> List[MentalHealthSignal]:
    """Merge rule-based and NLP-based signals."""
    if not nlp_based:
        return rule_based
    
    merged = rule_based.copy()
    
    # Add NLP signals that don't overlap with rule-based
    for nlp_signal in nlp_based:
        # Check for overlap
        overlap = False
        for rule_signal in rule_based:
            if rule_signal.indicator_type == nlp_signal.indicator_type:
                # Merge scores
                rule_signal.severity = (rule_signal.severity + nlp_signal.severity) / 2
                rule_signal.confidence = max(rule_signal.confidence, nlp_signal.confidence)
                overlap = True
                break
        
        if not overlap:
            merged.append(nlp_signal)
    
    return merged


def _calculate_confidence(score: float, keywords: List[str]) -> float:
    """Calculate confidence in signal detection."""
    if not keywords:
        return 0.3  # Low confidence if no keywords
    
    # More keywords = higher confidence
    keyword_factor = min(1.0, len(keywords) / 5.0)
    
    # Higher score = higher confidence
    score_factor = min(1.0, score / 7.0)
    
    # Combine factors
    confidence = (keyword_factor * 0.6 + score_factor * 0.4)
    
    return min(1.0, max(0.3, confidence))


# Initialize NLP models on module import (optional)
def initialize_nlp_models() -> bool:
    """Initialize NLP models for mental health signal detection."""
    return _nlp_manager.initialize()

