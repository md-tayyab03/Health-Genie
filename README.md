# HealthGenie - AI Powered Medical Assistant Chatbot

HealthGenie is a Streamlit-based chatbot that provides evidence-based medical information using Google's Gemini AI. It supports a dual-mode chat system for general and document-enhanced responses via RAG (Retrieval Augmented Generation).

## Features

### Dual Chat Modes
- 🔹 **Normal Mode**: Direct AI responses (Gemini)
- 🔹 **RAG Mode**: Enhanced answers using your medical documents
- Real-time AI chat with history + multi-session support
- Intuitive, clean UI with sidebar mode toggle
- Source citations when RAG mode is active

### Medical Knowledge Base
- Integrates vector embeddings from medical PDFs
- Supports multiple documents and custom chunking
- Based on LangChain + FAISS + Sentence-Transformers

## Setup

### 1. Prerequisites
- Python 3.11+
- Google API Key (for Gemini)

### 2. Clone & Install
```bash
git clone https://github.com/yourusername/Health-Genie.git
cd Health-Genie
python -m venv venv && source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file:
```ini
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Process Documents
```bash
# Create vectorstore from PDFs
python create_vectorstore.py --pdf_path "Data/*.pdf"
```

### 5. Run the App
```bash
streamlit run medibot.py
```

## Chat Mode Toggle

- Switch between Normal and RAG mode via sidebar
- RAG uses your medical documents for deeper insights
- View source documents for enhanced responses

## Tech Stack

- Python
- Streamlit
- Gemini AI
- LangChain
- FAISS
- PyPDF2
- Streamlit-Authenticator

## Contact

Feel free to Contribute🌟 For feedback or questions: mohammedtayyab242@gmail.com

## License

MIT License – see LICENSE


