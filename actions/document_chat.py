import json
import os
from pathlib import Path

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def get_api_key():
    key_file = get_base_dir() / 'config' / 'api_keys.json'
    try:
        with open(key_file, 'r') as f:
            data = json.load(f)
            return data.get('gemini_api_key')
    except (FileNotFoundError, json.JSONDecodeError):
        return None

try:
    import chromadb
    from chromadb import Documents, EmbeddingFunction, Embeddings
    from google import genai
except ImportError:
    chromadb = None
    genai = None

class CustomGeminiEmbeddingFunction:
    def __init__(self, key):
        from google import genai
        self.client = genai.Client(api_key=key)
    def __call__(self, input: list) -> list:
        response = self.client.models.embed_content(model='gemini-embedding-2', contents=input)
        return [e.values for e in response.embeddings]

def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def read_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
        except ImportError:
            return None, "PyPDF2 is not installed."
        except Exception as e:
            return None, f"Error reading PDF: {e}"
    elif ext == '.docx':
        try:
            import docx
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except ImportError:
            return None, "python-docx is not installed."
        except Exception as e:
            return None, f"Error reading DOCX: {e}"
    elif ext == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            return None, f"Error reading TXT: {e}"
    else:
        return None, f"Unsupported file type: {ext}"
    
    return text, None

def document_chat(parameters: dict, player=None) -> str:
    if not chromadb or not genai:
        return "ChromaDB or Google GenAI libraries are not installed, sir."
        
    action = parameters.get('action')
    db_path = get_base_dir() / 'chroma_db'
    db_path.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=str(db_path))
    
    api_key = get_api_key()
    if not api_key:
        return "Sir, I could not find the Gemini API key in the configuration."
        
    embed_fn = CustomGeminiEmbeddingFunction(api_key)
    
    if action == 'clear':
        try:
            client.delete_collection(name='document_chat')
            return "Document knowledge base has been cleared, sir."
        except ValueError:
            return "Knowledge base was already empty."
            
    elif action == 'load':
        file_path = parameters.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return "Please provide a valid file path, sir."
            
        text, err = read_file(file_path)
        if err:
            return err
            
        chunks = chunk_text(text)
        if not chunks:
            return "The document appears to be empty."
            
        collection = client.get_or_create_collection(name='document_chat', embedding_function=embed_fn)
        
        ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
        collection.add(documents=chunks, ids=ids)
        
        if player and hasattr(player, 'write_log'):
            player.write_log(f"Loaded {len(chunks)} chunks from {file_path}")
            
        return f"I have successfully ingested {os.path.basename(file_path)} into my knowledge base, sir."
        
    elif action == 'ask':
        query = parameters.get('query')
        if not query:
            return "Please provide a question, sir."
            
        try:
            collection = client.get_collection(name='document_chat', embedding_function=embed_fn)
        except ValueError:
            return "The knowledge base is empty. Please load a document first."
            
        results = collection.query(query_texts=[query], n_results=5)
        
        context = ""
        if results and results['documents'] and results['documents'][0]:
            context = "\n".join(results['documents'][0])
            
        if not context:
            return "I could not find any relevant information in the documents, sir."
            
        try:
            g_client = genai.Client(api_key=api_key)
            prompt = f"Context information is below.\n---------------------\n{context}\n---------------------\nGiven the context information, answer the query: {query}"
            response = g_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating answer: {e}"
            
    return "Invalid document chat action."
