import os
import google.generativeai as genai
from src.utils.logger import api_logger

class MultilingualHealthChat:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')

    def get_response(self, user_input: str, context: dict = None, language: str = "English"):
        if not self.model:
            return "AI Service Unavailable. Please check API keys."

        try:
            # Construct context-aware prompt
            patient_context = ""
            if context:
                patient_context = f"""
                Patient Context:
                - Age: {context.get('age')}
                - Risks: {context.get('risks')}
                - Symptoms: {context.get('symptoms')}
                """

            prompt = f"""
            You are 'Dr. Epi', a compassionate and knowledgeable AI Health Assistant.
            
            {patient_context}
            
            User Query: "{user_input}"
            
            Instructions:
            1. Answer the user's health question accurately.
            2. If the user speaks Hindi (or Hinglish), reply in Hindi (Devanagari script) mixed with English medical terms where appropriate.
            3. If the user speaks English, reply in English.
            4. Be empathetic but professional. Do not provide definitive medical diagnoses, but suggest next steps.
            5. Keep the response concise (under 100 words).
            
            Response:
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            api_logger.error(f"Chat generation failed: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
