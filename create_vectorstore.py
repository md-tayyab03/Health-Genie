import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def load_pdf_files(data_dir: str = "data"):
    """Load PDF files from the data directory."""
    print(f"Loading PDF files from {data_dir}...")
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")
    return documents

def create_chunks(documents, chunk_size=1000, chunk_overlap=100):
    """Split documents into chunks."""
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")
    return chunks

def create_vectorstore(chunks, output_dir: str = "vectorstore/medical_db"):
    """Create and save the vector store."""
    print("Initializing embedding model...")
    embedding_model = GoogleGenerativeAIEmbeddings(
        google_api_key=GOOGLE_API_KEY,
        model="models/embedding-001",
        api_version="v1beta"
    )

    print("Creating vector store...")
    vectorstore = FAISS.from_documents(chunks, embedding_model)
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_dir), exist_ok=True)
    
    print(f"Saving vector store to {output_dir}...")
    vectorstore.save_local(output_dir)
    print("Vector store created and saved successfully!")

def main():
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in environment variables")
        return

    try:
        # Create data directory if it doesn't exist
        if not os.path.exists("data"):
            os.makedirs("data")
            print("Created 'data' directory. Please add your medical PDF files to this directory.")
            return

        # Load PDF files
        documents = load_pdf_files()
        
        # Create chunks
        chunks = create_chunks(documents)
        
        # Create and save vector store
        create_vectorstore(chunks)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 