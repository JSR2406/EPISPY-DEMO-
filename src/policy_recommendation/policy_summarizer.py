"""
LLM-powered policy summarization.

This module provides functionality to summarize policies using LLM integration,
making policy information more accessible and easier to understand.
"""

from typing import Optional, Dict, Any
from ..utils.logger import api_logger


class PolicySummarizer:
    """
    Policy summarizer using LLM integration.
    
    Summarizes policy information, outcomes, and implementation guides
    using natural language generation.
    
    Example:
        summarizer = PolicySummarizer(ollama_client)
        summary = await summarizer.summarize_policy(policy, outcome)
    """
    
    def __init__(self, ollama_client: Optional[Any] = None):
        """
        Initialize policy summarizer.
        
        Args:
            ollama_client: Optional Ollama client for LLM operations
        """
        self.ollama_client = ollama_client
    
    async def summarize_policy(
        self,
        policy: Any,
        outcome: Optional[Any] = None,
        max_length: int = 500
    ) -> str:
        """
        Generate a natural language summary of a policy.
        
        Args:
            policy: Policy object
            outcome: Optional PolicyOutcome object
            max_length: Maximum summary length in characters
            
        Returns:
            Policy summary string
        """
        if not self.ollama_client:
            return self._fallback_summary(policy, outcome)
        
        try:
            # Build prompt
            prompt = self._build_summary_prompt(policy, outcome, max_length)
            
            # Generate summary using LLM
            summary = await self.ollama_client.generate_text(
                prompt=prompt,
                max_tokens=max_length // 4,  # Rough token estimate
                temperature=0.7
            )
            
            return summary.strip()
            
        except Exception as e:
            api_logger.warning(f"LLM summarization failed: {str(e)}, using fallback")
            return self._fallback_summary(policy, outcome)
    
    def _build_summary_prompt(
        self,
        policy: Any,
        outcome: Optional[Any],
        max_length: int
    ) -> str:
        """Build prompt for LLM summarization."""
        prompt = f"""Summarize the following epidemic response policy in {max_length} characters or less.

Policy Title: {policy.title}
Policy Type: {policy.policy_type.value}
Description: {policy.description[:500]}
Start Date: {policy.start_date}
Location: {policy.location.name if policy.location else 'Unknown'}, {policy.location.country if policy.location else ''}
"""
        
        if outcome:
            prompt += f"""
Effectiveness: {outcome.effectiveness_score}/10
Case Reduction: {outcome.case_reduction_percent if outcome.case_reduction_percent else 'N/A'}%
Death Reduction: {outcome.death_reduction_percent if outcome.death_reduction_percent else 'N/A'}%
Evidence Quality: {outcome.evidence_quality.value}
"""
        
        prompt += """
Provide a concise, informative summary that highlights:
1. What the policy does
2. Key outcomes/effectiveness (if available)
3. Important implementation details

Summary:"""
        
        return prompt
    
    def _fallback_summary(
        self,
        policy: Any,
        outcome: Optional[Any] = None
    ) -> str:
        """Generate fallback summary without LLM."""
        summary_parts = [
            f"{policy.title} ({policy.policy_type.value.replace('_', ' ').title()})",
            f"Implemented in {policy.location.name if policy.location else 'Unknown'}, {policy.location.country if policy.location else ''}",
        ]
        
        if policy.description:
            # Take first sentence or first 200 chars
            desc = policy.description.split('.')[0] if '.' in policy.description else policy.description[:200]
            summary_parts.append(desc)
        
        if outcome:
            summary_parts.append(
                f"Effectiveness: {outcome.effectiveness_score}/10 "
                f"(Evidence Quality: {outcome.evidence_quality.value})"
            )
            if outcome.case_reduction_percent:
                summary_parts.append(f"Reduced cases by {outcome.case_reduction_percent}%")
            if outcome.death_reduction_percent:
                summary_parts.append(f"Reduced deaths by {outcome.death_reduction_percent}%")
        
        return ". ".join(summary_parts) + "."
    
    async def generate_adaptation_guidance(
        self,
        policy: Any,
        target_context: Dict[str, Any],
        source_context: Dict[str, Any]
    ) -> str:
        """
        Generate adaptation guidance for implementing policy in target location.
        
        Args:
            policy: Policy object
            target_context: Target location context
            source_context: Source location context
            
        Returns:
            Adaptation guidance text
        """
        if not self.ollama_client:
            return self._fallback_adaptation_guidance(policy, target_context, source_context)
        
        try:
            prompt = f"""Generate adaptation guidance for implementing the following policy in a different context.

Policy: {policy.title}
Policy Description: {policy.description[:500]}

Source Location Context:
- GDP per capita: ${source_context.get('gdp_per_capita', 'N/A')}
- Healthcare capacity: {source_context.get('healthcare_capacity', 'N/A')}/10
- Population density: {source_context.get('population_density', 'N/A')} per km²
- Governance effectiveness: {source_context.get('governance_effectiveness', 'N/A')}/10

Target Location Context:
- GDP per capita: ${target_context.get('gdp_per_capita', 'N/A')}
- Healthcare capacity: {target_context.get('healthcare_capacity', 'N/A')}/10
- Population density: {target_context.get('population_density', 'N/A')} per km²
- Governance effectiveness: {target_context.get('governance_effectiveness', 'N/A')}/10

Provide specific, actionable guidance on how to adapt this policy for the target location, considering the differences in context.

Adaptation Guidance:"""
            
            guidance = await self.ollama_client.generate_text(
                prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )
            
            return guidance.strip()
            
        except Exception as e:
            api_logger.warning(f"LLM adaptation guidance failed: {str(e)}, using fallback")
            return self._fallback_adaptation_guidance(policy, target_context, source_context)
    
    def _fallback_adaptation_guidance(
        self,
        policy: Any,
        target_context: Dict[str, Any],
        source_context: Dict[str, Any]
    ) -> str:
        """Generate fallback adaptation guidance."""
        guidance_parts = []
        
        # Compare key factors
        if (target_context.get('gdp_per_capita') and source_context.get('gdp_per_capita') and
            target_context['gdp_per_capita'] < source_context['gdp_per_capita'] * 0.7):
            guidance_parts.append(
                "Consider cost-effective adaptations due to lower economic resources."
            )
        
        if (target_context.get('healthcare_capacity') and source_context.get('healthcare_capacity') and
            target_context['healthcare_capacity'] < source_context['healthcare_capacity'] * 0.8):
            guidance_parts.append(
                "May require additional healthcare support or phased implementation."
            )
        
        if (target_context.get('population_density') and source_context.get('population_density') and
            target_context['population_density'] > source_context['population_density'] * 1.5):
            guidance_parts.append(
                "Higher population density may require stricter enforcement measures."
            )
        
        if (target_context.get('governance_effectiveness') and source_context.get('governance_effectiveness') and
            target_context['governance_effectiveness'] < source_context['governance_effectiveness'] * 0.8):
            guidance_parts.append(
                "Consider simplified implementation approach given governance capacity."
            )
        
        if not guidance_parts:
            guidance_parts.append(
                "Contexts are similar - policy can be implemented with minimal adaptations."
            )
        
        return " ".join(guidance_parts)

