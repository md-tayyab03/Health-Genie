# HealthGenie - Medical Assistant Chatbot 🏥

HealthGenie is an AI-powered medical assistant chatbot built with Streamlit that provides evidence-based medical information and answers health-related questions. It features dual-mode operation: direct AI chat using Gemini and RAG-based (Retrieval Augmented Generation) chat using vector embeddings for enhanced domain-specific knowledge.

## Features

- *Dual-Mode Chat Interface*
  - Normal Mode: Direct AI chat using Google's Gemini
  - RAG Mode: Enhanced responses using vector embeddings from medical documents
  - Real-time chat with AI
  - Chat history preservation
  - Multiple chat sessions support
  - Clean and intuitive UI

- *Medical Knowledge Base*
  - Flexible knowledge source integration
  - Vector embedding-based document retrieval
  - Evidence-based responses
  - Medical encyclopedia integration

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. Initialize the configuration:
   Create a `config.yaml` file with initial admin credentials.

5. Set up Vector Database (for RAG mode):
   ```bash
   # Create vector embeddings from your PDF documents
   python create_vectorstore.py --pdf_path "Data/your_medical_docs.pdf"
   ```

6. Run the application:
   ```bash
   streamlit run medibot.py
   ```

## Tech Stack

- Python 3.9+
- Streamlit
- Google Gemini AI
- LangChain
- FAISS
- Sentence-Transformers
- PyPDF2
- Streamlit-Authenticator
- YAML
- HTML/CSS

## Vector Database Setup Commands

### Creating Vector Embeddings
```bash
# Basic usage
python create_vectorstore.py --pdf_path "Data/your_medical_docs.pdf"

# With custom chunk size and overlap
python create_vectorstore.py --pdf_path "Data/your_medical_docs.pdf" --chunk_size 1000 --chunk_overlap 200

# Process multiple PDFs
python create_vectorstore.py --pdf_path "Data/*.pdf"
```

### Switching Between Chat Modes

- Simple ON/OFF toggle button in the sidebar to switch RAG mode
- When RAG is ON: Responses are enhanced with medical document knowledge
- When RAG is OFF: Direct Gemini AI responses without document context
- Toggle at any time during conversation to switch modes
- Sources are displayed when RAG mode is active

### Using RAG Mode

1. Ensure your documents are processed (vector embeddings created)
2. Click the "ON" button in the sidebar to activate RAG mode
3. Your queries will now be answered using both AI and your medical documents
4. View sources used for responses when available
5. Switch back to normal mode anytime by clicking "OFF"

*Your contributions can help make healthcare information more accessible to everyone! 🌟*

For any queries, suggestions:
Email: **mohammedtayyab242@gmail.com**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

