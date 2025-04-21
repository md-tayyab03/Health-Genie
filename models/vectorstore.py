from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st
import os

class VectorStore:
    def __init__(self, path: str):
        self.path = path
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.embedding_model = None
        self.db = None

    @staticmethod
    @st.cache_resource
    def _load_vectorstore(path: str, api_key: str):
        """Static method to load the vector store with caching."""
        try:
            embedding_model = GoogleGenerativeAIEmbeddings(
                google_api_key=api_key,
                model="models/embedding-001",
                api_version="v1beta"
            )
            db = FAISS.load_local(path, embedding_model, allow_dangerous_deserialization=True)
            return db
        except Exception as e:
            st.error(f"Failed to load vector store: {str(e)}")
            return None

    def load(self):
        """Load the vector store."""
        self.db = self._load_vectorstore(self.path, self.api_key)
        return self.db

    def get_retriever(self, k: int = 2):
        """Get a retriever from the vector store."""
        if self.db is None:
            self.load()
        return self.db.as_retriever(search_kwargs={'k': k}) if self.db else None 