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

## Prerequisites

Before you begin, ensure you have:
- Python 3.11.6 or higher
- A Google API key for Gemini AI

## Setup Instructions

You can choose either method for setting up the project:

### Method 1: Using requirements.txt (Recommended for Deployment)
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/Health-Genie.git
   cd Health-Genie
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Method 2: Using Pipenv (Alternative for Local Development)
1. **Install Pipenv** (if not already installed)
   ```bash
   pip install pipenv
   ```

2. **Install Dependencies**
   ```bash
   pipenv install
   pipenv shell
   ```

### Common Setup Steps (After choosing either method)

1. **Environment Configuration**
   - Create a `.env` file in the project root:
     ```
     GOOGLE_API_KEY=your_google_api_key_here
     ```

2. **Initialize Vector Store**
   ```bash
   python create_vectorstore.py
   # Or with Pipenv:
   # pipenv run python create_vectorstore.py
   ```

3. **Run the Application**
   ```bash
   streamlit run medibot.py
   # Or with Pipenv:
   # pipenv run streamlit run medibot.py
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

## Acknowledgments

- Medical knowledge base from GALE Encyclopedia
- Powered by Google's Gemini AI
- Built with Streamlit and LangChain

## Development with Pipenv

- **Adding New Dependencies**
  ```bash
  pipenv install package_name
  ```

- **Adding Development Dependencies**
  ```bash
  pipenv install package_name --dev
  ```

- **Updating Dependencies**
  ```bash
  pipenv update
  ```

- **Generating requirements.txt** (for deployment)
  ```bash
  pipenv requirements > requirements.txt
  ```

## Deployment

1. **Prepare for Deployment**
   ```bash
   # Generate requirements.txt for deployment platforms
   pipenv requirements > requirements.txt
   ```

2. **Deploy to Streamlit Cloud**
   - Connect your GitHub repository
   - Set environment variables:
     - `GOOGLE_API_KEY`: Your Google API key

## Troubleshooting

- **Vector Store Issues**
  - If you encounter vector store loading issues:
    ```bash
    pipenv run python create_vectorstore.py
    ```

- **Dependency Issues**
  - Try cleaning and reinstalling:
    ```bash
    pipenv clean
    pipenv install
    ```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

