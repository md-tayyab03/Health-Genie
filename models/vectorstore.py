from typing import Optional
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

class VectorStore:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.embeddings = None
        self.vectorstore = None

    def initialize_embeddings(self) -> None:
        """Initialize the embeddings model."""
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=self.api_key,
            model="models/embedding-001",
            api_version="v1beta"
        )

    def load_vectorstore(self, path: str = "vectorstore/db_faiss") -> Optional[FAISS]:
        """Load the vector store from disk."""
        try:
            if not self.embeddings:
                self.initialize_embeddings()
            
            if os.path.exists(path):
                self.vectorstore = FAISS.load_local(
                    path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                return self.vectorstore
            return None
        except Exception as e:
            print(f"Error loading vector store: {str(e)}")
            return None

    def similarity_search(self, query: str, k: int = 3):
        """Perform similarity search on the vector store."""
        if self.vectorstore:
            return self.vectorstore.similarity_search(query, k=k)
        return None 