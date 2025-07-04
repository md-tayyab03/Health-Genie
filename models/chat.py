from dataclasses import dataclass
from typing import Optional, Tuple
import requests
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from .prompts import MEDICAL_QA_TEMPLATE
from pathlib import Path
import shutil

@dataclass
class ChatMessage:
    role: str
    content: str

class ChatBot:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.vectorstore = None  # Do not load on init

    @staticmethod
    @st.cache_resource(show_spinner=False)
    def _cached_load_vectorstore(api_key):
        from langchain_community.vectorstores import FAISS
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        import os
        print("[DEBUG] Attempting to load vectorstore...")
        embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=api_key,
            model="models/embedding-001",
            api_version="v1beta"
        )
        vectorstore_path = "vectorstore/db_faiss"
        if os.path.exists(vectorstore_path):
            try:
                vs = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
                print("[DEBUG] Vectorstore loaded successfully.")
                return vs
            except Exception as e:
                print(f"[ERROR] Error loading vectorstore: {e}")
                return None
        print(f"[WARNING] Vectorstore path not found: {vectorstore_path}")
        return None

    def ensure_vectorstore_loaded(self):
        if self.vectorstore is None:
            print("[DEBUG] Loading vectorstore via ensure_vectorstore_loaded...")
            self.vectorstore = self._cached_load_vectorstore(self.api_key)
            if self.vectorstore is None:
                print("[ERROR] Vectorstore could not be loaded!")

    def _detect_detail_level(self, query: str) -> str:
        """Detect if user is asking for detailed information."""
        detail_keywords = ['detail', 'explain', 'elaborate', 'comprehensive', 'thorough', 'in-depth']
        query_lower = query.lower()
        return "detailed" if any(keyword in query_lower for keyword in detail_keywords) else "concise"

    def get_rag_response(self, query: str, include_sources: bool = False) -> str:
        """Get response from RAG system with optional sources."""
        try:
            self.ensure_vectorstore_loaded()
            if not self.vectorstore:
                return "I apologize, but I'm having trouble accessing my medical knowledge base. Please try again in a few moments."

            # Get relevant documents
            docs = self.vectorstore.similarity_search(query, k=3)
            if not docs:
                return "I apologize, but I couldn't find relevant information for your query. Could you please rephrase your question?"

            # Summarize the content of the top chunks for a concise additional info section
            summary_points = []
            for doc in docs:
                text = doc.page_content.strip().replace('\n', ' ')
                # Take only the first 2-3 sentences for brevity
                sentences = text.split('. ')
                snippet = '. '.join(sentences[:2]) + ('.' if len(sentences) > 1 else '')
                summary_points.append(f"- {snippet}")

            # Get unique page numbers for sources
            page_numbers = sorted({doc.metadata.get('page', 'N/A') for doc in docs})
            page_range = f"Pages {page_numbers[0]}–{page_numbers[-1]}" if len(page_numbers) > 1 else f"Page {page_numbers[0]}"

            response = "\n".join(summary_points)
            if include_sources:
                response += f"\n\nSources: Data\\GALE_ENCYCLOPEDIA.pdf ({page_range})"
            return response

        except Exception as e:
            # If vector store fails during query, try to reload once
            try:
                self.vectorstore = self._cached_load_vectorstore(self.api_key)
                if self.vectorstore:
                    return self.get_rag_response(query, include_sources)
            except:
                pass
            return "I apologize, but I'm having trouble processing your request. Please try again."

    def _get_gemini_response(self, prompt: str) -> str:
        """Get response from Gemini API."""
        try:
            url = f"{self.base_url}?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            
            # Enhanced configuration for more detailed responses
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048  # Increased for longer responses
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                return f"API Error: {response.text}"

            result = response.json()
            if 'candidates' in result:
                return result['candidates'][0]['content']['parts'][0]['text']
            return "No response generated"

        except Exception as e:
            return f"Failed to generate response : {str(e)}"

    def get_general_response(self, query: str) -> str:
        """Get general response from Gemini without references."""
        # Create a prompt that asks the model to provide information in our template format
        system_prompt = f"""You are a medical AI assistant. Answer the following medical question:
{query}

Provide your response in the following format, filling in all sections:
{MEDICAL_QA_TEMPLATE}"""
        
        return self._get_gemini_response(system_prompt)

    def _analyze_query_type(self, query: str) -> dict:
        """Analyze the query to determine the type of response needed."""
        query_lower = query.lower()
        
        # Check for detail level
        detail_keywords = ['detail', 'explain', 'elaborate', 'comprehensive', 'thorough', 'in-depth']
        is_detailed = any(keyword in query_lower for keyword in detail_keywords)
        
        # Check for list request
        list_keywords = ['list', 'what are', 'types of', 'kinds of', 'ways to', 'steps', 'methods']
        is_list = any(keyword in query_lower for keyword in list_keywords)
        
        # Check for definition/explanation
        what_is = any(x in query_lower for x in ['what is', 'what are', 'define', 'meaning of', 'tell me about'])
        
        # Check for comparison
        compare = any(x in query_lower for x in ['compare', 'difference', 'versus', 'vs', 'better'])
        
        return {
            "detailed": is_detailed,
            "list": is_list,
            "what_is": what_is,
            "compare": compare
        }

    def generate_response(self, prompt: str, message_history: list, show_sources: bool = False) -> Optional[Tuple[str, str]]:
        """Generate responses using our detailed template."""
        try:
            with st.spinner("Thinking..."):
                # Analyze the query type
                query_type = self._analyze_query_type(prompt)
                
                # Create context from message history
                context = "\n".join([
                    f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                    for msg in message_history[-4:]
                ])
                
                # Customize the instruction based on query type
                style_instruction = ""
                if query_type["detailed"]:
                    style_instruction = "Provide a detailed, comprehensive response with thorough explanations."
                elif query_type["list"]:
                    style_instruction = "Structure your response as a clear, organized list with bullet points where appropriate."
                elif query_type["what_is"]:
                    style_instruction = "Focus on providing a clear, concise definition and basic explanation first, then add details."
                elif query_type["compare"]:
                    style_instruction = "Structure your response to clearly compare and contrast the relevant aspects."
                
                # Create a prompt that asks the model to provide information in our template format
                system_prompt = f"""You are a medical AI assistant. Consider this conversation context and answer the latest question:

Previous conversation:
{context}

Latest question: {prompt}

{style_instruction}

Provide your response in the following format, filling in all sections appropriately:
{MEDICAL_QA_TEMPLATE}

Remember to:
- Keep the Brief Answer section concise but informative
- Use bullet points and lists where appropriate
- Highlight important warnings or considerations
- Include relevant medical terms with their explanations
- Structure the information in an easy-to-read format"""
                
                base_response = self._get_gemini_response(system_prompt)
                
                # If sources are requested, get RAG response and combine
                if show_sources:
                    rag_response = self.get_rag_response(prompt, include_sources=True)
                    if rag_response and "No medical documents available" not in rag_response:
                        final_response = f"{base_response}\n\n📚 **Additional Research & Sources:**\n{rag_response}"
                    else:
                        final_response = base_response
                else:
                    final_response = base_response
                
                return base_response, final_response

        except Exception as e:
            st.error(f"Failed to generate response: {str(e)}")
            return None

    def _format_response(self, text: str) -> str:
        """Format the response if it doesn't follow the template structure."""
        sections = text.split('\n\n')
        formatted_response = """
🏥 **Overview:**
{}

📋 **Detailed Information:**
{}

⚕️ **Medical Considerations:**
{}

⚠️ **Important Warnings:**
{}

💡 **Professional Tips:**
{}

🔍 **Scientific Evidence:**
{}

📚 **References:**
{}
""".format(
            sections[0] if sections else "Information not available",
            '\n'.join(sections[1:3]) if len(sections) > 2 else "Details not available",
            sections[3] if len(sections) > 3 else "Medical considerations not available",
            sections[4] if len(sections) > 4 else "Warning information not available",
            sections[5] if len(sections) > 5 else "Professional tips not available",
            sections[6] if len(sections) > 6 else "Scientific evidence not available",
            sections[7] if len(sections) > 7 else "References not available"
        )
        return formatted_response