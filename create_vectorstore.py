import os
import shutil
import time
from pathlib import Path
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

def create_new_vectorstore():
    """Create a new vector store from the medical knowledge base PDF."""
    start_time = time.time()
    
    # Load environment variables
    print("Loading environment variables...")
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables")
        return False
    
    try:
        print("🔄 Initializing embeddings model...")
        embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=api_key,
            model="models/embedding-001",
            api_version="v1beta"
        )
        print("✅ Embeddings model initialized successfully")
        
        vectorstore_path = Path("vectorstore/db_faiss")
        
        # Clean up existing vectorstore if it exists
        if vectorstore_path.exists():
            print("🗑️ Removing existing vector store...")
            shutil.rmtree(vectorstore_path, ignore_errors=True)
            print("✅ Old vector store removed")
        
        # Create new vectorstore
        print("\n🔄 Starting new vector store creation...")
        pdf_path = Path("Data/GALE_ENCYCLOPEDIA.pdf")
        if not pdf_path.exists():
            pdf_path = Path("data/GALE_ENCYCLOPEDIA.pdf")
            if not pdf_path.exists():
                print("❌ Error: Medical knowledge base PDF not found. Please ensure GALE_ENCYCLOPEDIA.pdf is in the Data/ directory.")
                return False
        
        print(f"📚 Loading PDF from: {pdf_path}")
        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        print(f"✅ Successfully loaded {len(documents)} pages from PDF")
        
        print("\n🔄 Using per-page chunking for accurate page numbers...")
        chunks = []
        for i, doc in enumerate(documents):
            doc.metadata['page'] = i + 1  # 1-based page numbers
            chunks.append(doc)
        print(f"✅ Created {len(chunks)} per-page chunks")
        
        if not chunks:
            print("❌ Error: No content extracted from PDF")
            return False
        
        print("\n🔄 Creating FAISS vector store...")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        print("✅ Vector store created in memory")
        
        # Ensure directory exists
        vectorstore_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("\n🔄 Saving vector store to disk...")
        vectorstore.save_local(str(vectorstore_path))
        print(f"✅ Vector store saved to {vectorstore_path}")
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        print(f"\n🎉 Process completed successfully in {duration} seconds!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating vector store: {str(e)}")
        import traceback
        print("\nDetailed error traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 Starting vector store creation process...\n")
    success = create_new_vectorstore()
    if success:
        print("\n✨ Vector store creation completed successfully!")
    else:
        print("\n❌ Vector store creation failed!") 