import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from src.utils.logger import api_logger

class MedicalKnowledgeBase:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.vector_store = None
        self.is_ready = False
        
        if self.api_key:
            try:
                self._initialize_knowledge_base()
            except Exception as e:
                api_logger.error(f"Failed to initialize Medical Knowledge Base: {e}")

    def _initialize_knowledge_base(self):
        # Simulated medical guidelines (In a real app, this would ingest PDFs)
        guidelines = [
            "Diabetes Management: For HbA1c > 6.5%, initiate lifestyle changes. Metformin is first-line therapy.",
            "Hypertension: Stage 1 is 130-139/80-89. Recommended DASH diet and sodium restriction.",
            "Heart Disease: Chest pain requires immediate ECG. Statins recommended for LDL > 100.",
            "Cancer Screening: Mammograms recommended annually for women 45-54. Colonoscopy every 10 years after 45.",
            "Rare Diseases: Unexplained weight loss and night sweats may indicate lymphoma or tuberculosis.",
            "Pediatric: Fever > 38C in infants < 3 months requires immediate ER evaluation.",
            "Mental Health: PHQ-9 score > 10 indicates moderate depression. Consider CBT."
        ]
        
        docs = [Document(page_content=g, metadata={"source": "Clinical Guidelines 2024"}) for g in guidelines]
        
        embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        self.vector_store = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name="medical_guidelines"
        )
        self.is_ready = True
        api_logger.info("Medical Knowledge Base (RAG) initialized.")

    def search(self, query: str, k: int = 2):
        if not self.is_ready:
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            api_logger.error(f"RAG Search failed: {e}")
            return []
