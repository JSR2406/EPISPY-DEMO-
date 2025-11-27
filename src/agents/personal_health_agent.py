"""
Personal Health Agent - EpiSPY

AI agent that provides personalized health coaching, answers risk questions,
and provides mental health support referrals.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.resource_models import UserProfile, RiskHistory
from ..personalized.risk_calculator import PersonalizedRiskCalculator
from ..personalized.notification_service import NotificationManager, NotificationType
from ..utils.logger import api_logger


class PersonalHealthAgent:
    """
    AI agent for personalized health assistance.
    
    Capabilities:
    - Answer risk-related questions
    - Provide personalized health coaching
    - Recommend testing based on symptoms
    - Mental health support referrals
    - Travel risk assessment
    - Health advice generation
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize personal health agent.
        
        Args:
            session: Database session
        """
        self.session = session
        self.risk_calculator = PersonalizedRiskCalculator(session)
        self.notification_manager = NotificationManager(session)
    
    async def answer_risk_question(
        self,
        user_id: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Answer a risk-related question from the user.
        
        Args:
            user_id: User identifier
            question: User's question
            
        Returns:
            Answer with risk assessment
        """
        api_logger.info(f"Personal health agent: Answering question for user {user_id}")
        
        question_lower = question.lower()
        
        # Get user's current risk
        risk_result = await self.risk_calculator.calculate_risk_score(user_id)
        
        # Simple question answering (can be enhanced with LLM)
        answer = ""
        recommendations = []
        
        if "risk" in question_lower or "safe" in question_lower:
            answer = (
                f"Your current risk level is {risk_result.risk_level} "
                f"with a score of {risk_result.total_score:.1f}/100. "
            )
            
            if risk_result.risk_level == "CRITICAL":
                answer += "You should take immediate protective measures."
                recommendations = risk_result.recommendations[:3]
            elif risk_result.risk_level == "HIGH":
                answer += "Please take extra precautions."
                recommendations = risk_result.recommendations[:2]
            else:
                answer += "Continue following standard health guidelines."
                recommendations = risk_result.recommendations[:1]
        
        elif "test" in question_lower or "testing" in question_lower:
            if risk_result.exposure_risk > 50 or risk_result.total_score > 60:
                answer = "Yes, we recommend getting tested based on your risk profile."
                recommendations = ["Get tested at nearest testing center", "Self-isolate until results"]
            else:
                answer = "Testing may not be necessary unless you have symptoms."
                recommendations = ["Monitor symptoms", "Get tested if symptoms develop"]
        
        elif "travel" in question_lower or "visit" in question_lower:
            answer = "Please use the travel risk assessment feature for specific destinations."
            recommendations = ["Use /personal/travel/assess endpoint for detailed travel risk"]
        
        elif "symptom" in question_lower:
            answer = "If you're experiencing symptoms, please report them using the report-symptoms endpoint."
            recommendations = ["Report symptoms immediately", "Consider getting tested"]
        
        else:
            answer = (
                f"Based on your current risk profile ({risk_result.risk_level}), "
                "here are some general recommendations:"
            )
            recommendations = risk_result.recommendations[:3]
        
        return {
            'question': question,
            'answer': answer,
            'current_risk': {
                'level': risk_result.risk_level,
                'score': risk_result.total_score,
            },
            'recommendations': recommendations,
            'answered_at': datetime.now().isoformat(),
        }
    
    async def provide_health_coaching(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Provide personalized health coaching.
        
        Args:
            user_id: User identifier
            
        Returns:
            Health coaching advice
        """
        api_logger.info(f"Personal health agent: Providing health coaching for user {user_id}")
        
        # Get user profile
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return {
                'message': 'Please create a profile for personalized coaching',
                'coaching': [],
            }
        
        # Get current risk
        risk_result = await self.risk_calculator.calculate_risk_score(user_id)
        
        # Generate personalized coaching
        coaching_points = []
        
        # Age-based advice
        if profile.age_group:
            if profile.age_group in ['51-65', '65+']:
                coaching_points.append({
                    'category': 'Age',
                    'advice': 'As you are in a higher-risk age group, consider additional precautions.',
                    'actions': ['Wear N95 masks in public', 'Avoid crowded places', 'Get vaccinated/boosted'],
                })
        
        # Comorbidity advice
        if profile.comorbidities:
            coaching_points.append({
                'category': 'Health Conditions',
                'advice': 'Your health conditions may increase risk. Monitor closely.',
                'actions': ['Consult with healthcare provider', 'Ensure medication supply', 'Monitor symptoms daily'],
            })
        
        # Vaccination advice
        if not profile.vaccination_status or (
            isinstance(profile.vaccination_status, dict) and
            profile.vaccination_status.get('doses', 0) < 2
        ):
            coaching_points.append({
                'category': 'Vaccination',
                'advice': 'Getting fully vaccinated significantly reduces risk.',
                'actions': ['Schedule vaccination appointment', 'Complete full vaccination series'],
            })
        
        # Risk level advice
        if risk_result.risk_level in ['HIGH', 'CRITICAL']:
            coaching_points.append({
                'category': 'Current Risk',
                'advice': f'Your risk level is {risk_result.risk_level}. Take immediate action.',
                'actions': risk_result.recommendations[:3],
            })
        
        return {
            'user_id': user_id,
            'current_risk_level': risk_result.risk_level,
            'coaching_points': coaching_points,
            'generated_at': datetime.now().isoformat(),
        }
    
    async def recommend_testing(
        self,
        user_id: str,
        symptoms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Recommend testing based on risk and symptoms.
        
        Args:
            user_id: User identifier
            symptoms: Optional list of symptoms
            
        Returns:
            Testing recommendation
        """
        api_logger.info(f"Personal health agent: Recommending testing for user {user_id}")
        
        # Get current risk
        risk_result = await self.risk_calculator.calculate_risk_score(user_id)
        
        # Determine if testing is recommended
        testing_recommended = False
        urgency = "ROUTINE"
        reasons = []
        
        if symptoms:
            testing_recommended = True
            urgency = "URGENT"
            reasons.append("You reported symptoms")
        
        if risk_result.exposure_risk > 50:
            testing_recommended = True
            urgency = "URGENT"
            reasons.append("Recent potential exposure detected")
        
        if risk_result.total_score > 70:
            testing_recommended = True
            urgency = "URGENT" if risk_result.total_score > 85 else "ROUTINE"
            reasons.append(f"High risk level ({risk_result.risk_level})")
        
        # Get user profile for location
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        recommendation = {
            'testing_recommended': testing_recommended,
            'urgency': urgency,
            'reasons': reasons,
            'current_risk_score': risk_result.total_score,
            'current_risk_level': risk_result.risk_level,
            'next_steps': [],
        }
        
        if testing_recommended:
            recommendation['next_steps'] = [
                'Find nearest testing center',
                'Schedule testing appointment',
                'Self-isolate until tested' if urgency == "URGENT" else 'Monitor symptoms',
                'Follow up with healthcare provider',
            ]
            
            # Send notification
            await self.notification_manager.send_notification(
                user_id=user_id,
                notification_type=NotificationType.TESTING_RECOMMENDATION,
                title="Testing Recommended",
                message=f"Based on your risk profile, we recommend getting tested. Urgency: {urgency}",
                priority=urgency,
            )
        else:
            recommendation['next_steps'] = [
                'Continue monitoring symptoms',
                'Maintain standard precautions',
            ]
        
        return recommendation
    
    async def provide_mental_health_support(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Provide mental health support and referrals.
        
        Args:
            user_id: User identifier
            
        Returns:
            Mental health resources and referrals
        """
        api_logger.info(f"Personal health agent: Providing mental health support for user {user_id}")
        
        # Get current risk
        risk_result = await self.risk_calculator.calculate_risk_score(user_id)
        
        # Mental health resources
        resources = {
            'crisis_hotline': '988',  # National crisis line
            'resources': [
                'National Suicide Prevention Lifeline: 988',
                'Crisis Text Line: Text HOME to 741741',
                'Mental Health America: mhanational.org',
            ],
            'self_care_tips': [
                'Maintain regular routine',
                'Stay connected with loved ones',
                'Practice mindfulness and relaxation',
                'Limit news consumption',
                'Get adequate sleep',
            ],
        }
        
        # Adjust based on risk level
        if risk_result.risk_level in ['HIGH', 'CRITICAL']:
            resources['urgent_care'] = True
            resources['message'] = (
                "High stress levels detected. Please reach out for support. "
                "You're not alone, and help is available."
            )
        else:
            resources['urgent_care'] = False
            resources['message'] = "Remember to take care of your mental health during these times."
        
        return resources
    
    async def assess_travel_risk(
        self,
        user_id: str,
        destination_lat: float,
        destination_lon: float
    ) -> Dict[str, Any]:
        """
        Assess travel risk for a specific destination.
        
        Args:
            user_id: User identifier
            destination_lat: Destination latitude
            destination_lon: Destination longitude
            
        Returns:
            Travel risk assessment
        """
        api_logger.info(f"Personal health agent: Assessing travel risk for user {user_id}")
        
        # Calculate risk at destination
        risk_result = await self.risk_calculator.calculate_risk_score(
            user_id,
            (destination_lat, destination_lon)
        )
        
        # Get user profile
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        # Generate travel advice
        travel_advice = []
        
        if risk_result.risk_level == "CRITICAL":
            travel_advice.append("URGENT: Consider postponing non-essential travel")
            travel_advice.append("If travel is essential, take maximum precautions")
        elif risk_result.risk_level == "HIGH":
            travel_advice.append("Travel is not recommended unless essential")
            travel_advice.append("If traveling, get tested before and after")
        else:
            travel_advice.append("Travel may be possible with precautions")
            travel_advice.append("Follow all local health guidelines")
        
        # Requirements
        requirements = {
            'testing_required': risk_result.risk_level in ['HIGH', 'CRITICAL'],
            'quarantine_required': risk_result.risk_level == 'CRITICAL',
            'vaccination_proof': True,
            'mask_mandate': True,
        }
        
        return {
            'destination_risk': {
                'score': risk_result.total_score,
                'level': risk_result.risk_level,
            },
            'travel_advice': travel_advice,
            'requirements': requirements,
            'recommendations': risk_result.recommendations,
        }

