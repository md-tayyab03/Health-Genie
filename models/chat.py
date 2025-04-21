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
        self.vectorstore = self._load_vectorstore()

    def _load_vectorstore(self) -> FAISS:
        """Load the FAISS vector store."""
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                google_api_key=self.api_key,
                model="models/embedding-001",
                api_version="v1beta"
            )
            vectorstore_path = "vectorstore/db_faiss"
            
            # Check for vector store lock file
            lock_file = "vectorstore/creation_lock"
            
            # If vector store exists and no lock file, try to load it
            if os.path.exists(vectorstore_path) and not os.path.exists(lock_file):
                try:
                    return FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
                except Exception as e:
                    st.error(f"Error loading vector store: {str(e)}")
                    st.info("Using backup vector store...")
                    # Try to load from backup if exists
                    backup_path = "vectorstore/db_faiss_backup"
                    if os.path.exists(backup_path):
                        try:
                            return FAISS.load_local(backup_path, embeddings, allow_dangerous_deserialization=True)
                        except:
                            st.error("Backup vector store also failed to load.")
                    
                    # If we get here, both main and backup failed
                    st.warning("Creating new vector store. This may take a few minutes...")
            
            # Create lock file to prevent multiple processes from creating vector store simultaneously
            Path(lock_file).touch()
            
            try:
                # Create new vectorstore
                pdf_path = os.path.join("Data", "GALE_ENCYCLOPEDIA.pdf")
                if not os.path.exists(pdf_path):
                    pdf_path = os.path.join("data", "GALE_ENCYCLOPEDIA.pdf")
                    if not os.path.exists(pdf_path):
                        st.error("Medical knowledge base PDF not found.")
                        if os.path.exists(lock_file):
                            os.remove(lock_file)
                        return None
                
                from langchain_community.document_loaders import PyPDFLoader
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                
                # Load PDF
                loader = PyPDFLoader(pdf_path)
                documents = loader.load()
                
                # Split documents with smaller chunks for better handling
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50
                )
                chunks = text_splitter.split_documents(documents)
                
                if not chunks:
                    st.error("No content extracted from PDF.")
                    if os.path.exists(lock_file):
                        os.remove(lock_file)
                    return None
                
                # Create new vectorstore
                vectorstore = FAISS.from_documents(chunks, embeddings)
                
                # Backup existing vector store if it exists
                if os.path.exists(vectorstore_path):
                    backup_path = "vectorstore/db_faiss_backup"
                    if os.path.exists(backup_path):
                        shutil.rmtree(backup_path)
                    shutil.copytree(vectorstore_path, backup_path)
                
                # Save new vector store
                os.makedirs(vectorstore_path, exist_ok=True)
                vectorstore.save_local(vectorstore_path)
                st.success("Vector store created successfully!")
                
                # Remove lock file after successful creation
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                
                return vectorstore
                
            except Exception as create_error:
                st.error(f"Failed to create vector store: {str(create_error)}")
                # Remove lock file if creation fails
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                return None
                
        except Exception as e:
            st.error(f"Failed to initialize vector store: {str(e)}")
            # Remove lock file if initialization fails
            if os.path.exists("vectorstore/creation_lock"):
                os.remove("vectorstore/creation_lock")
            return None

    def _detect_detail_level(self, query: str) -> str:
        """Detect if user is asking for detailed information."""
        detail_keywords = ['detail', 'explain', 'elaborate', 'comprehensive', 'thorough', 'in-depth']
        query_lower = query.lower()
        return "detailed" if any(keyword in query_lower for keyword in detail_keywords) else "concise"

    def get_rag_response(self, query: str, include_sources: bool = False) -> str:
        """Get response from RAG system with optional sources."""
        try:
            if not self.vectorstore:
                return "No medical documents available for reference."

            # Get relevant documents
            docs = self.vectorstore.similarity_search(query, k=3)
            if not docs:
                return "No relevant information found in medical documents."

            # Format documents for context
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Create response with sources
            response_parts = []
            
            # Add main content
            response_parts.append("Based on medical literature:")
            response_parts.append(context)
            
            # Add sources if requested
            if include_sources:
                response_parts.append("\nSources:")
                for doc in docs:
                    source = doc.metadata.get('source', 'Unknown')
                    page = doc.metadata.get('page', 'Unknown')
                    response_parts.append(f"- {source} (Page {page})")
            
            return "\n".join(response_parts)

        except Exception as e:
            return f"Error in RAG response: {str(e)}"

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