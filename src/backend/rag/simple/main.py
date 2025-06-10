from fastapi import FastAPI, File, UploadFile # Added File, UploadFile
from pydantic import BaseModel
import os
import torch
from dotenv import load_dotenv
from huggingface_hub import login
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict # Corrected from List, Dict
import shutil # Added for file operations
import fitz  # PyMuPDF for PDF parsing
from langchain.text_splitter import RecursiveCharacterTextSplitter # For text chunking

# 0. Environment Setup
load_dotenv()
HF_TOKEN = os.getenv('HF_TOKEN')
if HF_TOKEN:
    login(token=HF_TOKEN)
else:
    print("HF_TOKEN not found. Skipping Hugging Face login.")

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f'Using device: {device}')

# === Directories for PDF uploads and their vector stores ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, "uploaded_pdfs")
VECTOR_STORE_BASE_DIR = os.path.join(BASE_DIR, "pdf_vector_stores")

# Create directories if they don't exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(VECTOR_STORE_BASE_DIR, exist_ok=True)
# End ===

# 1. FastAPI App and Pydantic Models
app = FastAPI()

class QueryRequest(BaseModel):
    pdf_filename: str # Changed from paper_id
    question: str

class AnswerResponse(BaseModel):
    ai_answer: str
    # Optional: add source documents or other info if needed
    # top_docs: List[str] = [] 

# 2. Global Variables and Model Initialization (Encoder, LLM, Reranker)

# SentenceTransformer encoder will be loaded once globally
encoder = None
try:
    encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device=device)
    print("SentenceTransformer encoder loaded successfully.")
except Exception as e:
    print(f"Error initializing SentenceTransformer encoder: {e}")
    # Application might not be usable if encoder fails to load. Consider raising an error.

# LLM and Reranker Setup (global instances)
ce_reranker = None
llm = None
try:
    ce_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device=device)
    print("CrossEncoder reranker loaded successfully.")
except Exception as e:
    print(f"Error initializing CrossEncoder: {e}")

try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.0
    )
    print("ChatGoogleGenerativeAI LLM loaded successfully.")
except Exception as e:
    print(f"Error initializing ChatGoogleGenerativeAI: {e}")


# === PDF Processing Function ===
def process_and_embed_pdf(pdf_path: str, pdf_filename: str):
    """
    Parses a PDF, chunks its text, creates embeddings, and stores them in a PDF-specific ChromaDB.
    """
    if encoder is None:
        print("Error: SentenceTransformer encoder not loaded. Cannot process PDF.")
        return False

    print(f"Processing PDF: {pdf_filename}")
    specific_db_path = os.path.join(VECTOR_STORE_BASE_DIR, f"{pdf_filename}_db")
    
    # Create a subdirectory for this PDF's ChromaDB if it doesn't exist
    os.makedirs(specific_db_path, exist_ok=True)

    try:
        # 1. Parse PDF
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        if not full_text.strip():
            print(f"No text found in PDF: {pdf_filename}")
            return False

        # 2. Chunk Text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(full_text)

        if not chunks:
            print(f"Could not split text into chunks for PDF: {pdf_filename}")
            return False
        
        print(f"PDF '{pdf_filename}' split into {len(chunks)} chunks.")

        # 3. Embed Chunks
        embeddings = encoder.encode(chunks, show_progress_bar=True)

        # 4. Store in ChromaDB
        # Each PDF gets its own ChromaDB client and collection in its specific directory
        pdf_client = chromadb.PersistentClient(path=specific_db_path)
        # Using a consistent collection name within each PDF's DB
        collection_name = "pdf_content" 
        
        # Check if collection exists, if so, clear it for re-processing (or decide on update strategy)
        try:
            # pdf_client.delete_collection(name=collection_name) # Option: Clear before re-adding
            # print(f"Cleared existing collection '{collection_name}' for {pdf_filename}")
            collection = pdf_client.get_collection(name=collection_name)
            # If re-uploading, consider clearing old entries or versioning.
            # For simplicity, we'll upsert, which can overwrite or add.
            # If you want to ensure a clean slate on re-upload, uncomment delete_collection or handle IDs.
        except: # chromadb.errors.CollectionNotFoundError or similar
            print(f"Creating new collection '{collection_name}' for {pdf_filename}")
        
        collection = pdf_client.get_or_create_collection(name=collection_name)

        # Prepare IDs and metadatas for ChromaDB
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": pdf_filename, "chunk_index": i} for i in range(len(chunks))]

        collection.upsert(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=metadatas
        )
        print(f"Successfully embedded and stored {len(chunks)} chunks for PDF: {pdf_filename} in {specific_db_path}")
        return True

    except Exception as e:
        print(f"Error processing PDF {pdf_filename}: {e}")
        import traceback
        traceback.print_exc()
        return False
# End PDF Processing Function ===


# === FastAPI Endpoint for PDF Upload ===
@app.post("/upload_pdf/")
async def upload_pdf_endpoint(file: UploadFile = File(...)):
    print(f"Received file upload: {file.filename}")
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Invalid file type. Only PDF files are accepted."}

    upload_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    
    # Save the uploaded file
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {"error": f"Failed to save uploaded file: {e}"}
    finally:
        file.file.close()

    # Process and embed the saved PDF
    success = process_and_embed_pdf(upload_path, file.filename)
    if success:
        return {"message": f"PDF '{file.filename}' uploaded and processed successfully."}
    else:
        # Optionally, clean up the saved PDF if processing failed
        # os.remove(upload_path) 
        return {"error": f"Failed to process PDF '{file.filename}'. Check server logs."}
# End PDF Upload Endpoint ===


# 3. LangGraph Setup

# State Definition
class InputState(TypedDict):
    pdf_filename: str # Changed from paper_id
    question: str

class OutputState(TypedDict):
    pdf_filename: str # Pass through pdf_filename
    answer: str
    top_docs: List[str]
    top_metadatas: List[Dict]

class OverallState(InputState, OutputState):
    retrieved_docs: List[str]
    retrieved_metadatas: List[Dict]

# Node Functions
def retrieve(state: OverallState) -> OverallState:
    if encoder is None: # Encoder is needed for query embedding
        print("Error: SentenceTransformer encoder not loaded. Cannot retrieve.")
        state["retrieved_docs"] = []
        state["retrieved_metadatas"] = []
        state["answer"] = "Error: Backend search service (encoder) not available."
        return state

    pdf_filename = state["pdf_filename"]
    question = state["question"]
    print(f"Retrieving for PDF: {pdf_filename}, question: {question[:50]}...")

    specific_db_path = os.path.join(VECTOR_STORE_BASE_DIR, f"{pdf_filename}_db")

    if not os.path.exists(specific_db_path):
        print(f"Error: Vector store for PDF '{pdf_filename}' not found at {specific_db_path}. Please upload and process the PDF first.")
        state["retrieved_docs"] = []
        state["retrieved_metadatas"] = []
        state["answer"] = f"Error: PDF '{pdf_filename}' not processed. Please upload it first."
        return state

    try:
        # Connect to ChromaDB
        pdf_client = chromadb.PersistentClient(path=specific_db_path)
        collection_name = "pdf_content" # Consistent collection name
        current_collection = pdf_client.get_collection(name=collection_name)
        
        q_emb = encoder.encode(question)

        res = current_collection.query(
            query_embeddings=[q_emb.tolist()],
            n_results=10, # Reduced n_results for typical PDF context
            include=["documents", "metadatas"]
            # TODO : 'where' clause needed to DB can specify which PDF to search in.
            # TODO : at this point, query is single hop, PDF-specific.
        )
        
        retrieved_docs = res["documents"][0] if res.get("documents") and res["documents"][0] else []
        retrieved_metadatas = res["metadatas"][0] if res.get("metadatas") and res["metadatas"][0] else []
        
        state["retrieved_docs"] = retrieved_docs
        state["retrieved_metadatas"] = retrieved_metadatas
        if not retrieved_docs: # If no docs, set answer to unanswerable early
            state["answer"] = "unanswerable"


    except Exception as e:
        print(f"Error during ChromaDB query for {pdf_filename}: {e}")
        state["retrieved_docs"] = []
        state["retrieved_metadatas"] = []
        state["answer"] = "Error: Could not retrieve documents from the PDF's database."

    print(f"Retrieved {len(state.get('retrieved_docs', []))} documents for {pdf_filename}.")
    return state

def rerank(state: OverallState) -> OverallState:
    if ce_reranker is None:
        print("Warning: Reranker not initialized. Skipping rerank.")
        state["top_docs"] = state.get("retrieved_docs", [])[:5] # Pass through top 5 if no reranker
        state["top_metadatas"] = state.get("retrieved_metadatas", [])[:5]
        # Do not set answer here if retrieve already set one (e.g. error or unanswerable)
        return state
    
    # If retrieve already set an answer (e.g. error or unanswerable because no docs found), pass it through
    if "answer" in state and state["answer"] != "Error: Could not retrieve documents from the PDF's database.": # Avoid overwriting specific retrieval error
        if state["answer"] == "unanswerable" or "Error:" in state["answer"]:
             print(f"Skipping rerank due to prior state: {state['answer']}")
             state["top_docs"] = state.get("retrieved_docs", []) 
             state["top_metadatas"] = state.get("retrieved_metadatas", [])
             return state


    print("Reranking documents...")
    docs = state.get("retrieved_docs", [])
    metadatas = state.get("retrieved_metadatas", [])
    q = state["question"]

    if not docs:
        state["top_docs"] = []
        state["top_metadatas"] = []
        print("No documents to rerank.")
        if "answer" not in state: # If no prior answer set
            state["answer"] = "unanswerable"
        return state

    try:
        scores = ce_reranker.predict([(q, d) for d in docs])
        # Ensure scores and docs align if docs list was empty or very short
        if not isinstance(scores, list) and not isinstance(scores, type(torch.empty(0).numpy())): # Check if scores is a numpy array
             scores = scores.tolist()


        scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        
        # Select top N
        top_n = 20
        state["top_docs"] = [docs[idx] for idx, _ in scored_indices[:top_n]]
        state["top_metadatas"] = [metadatas[idx] for idx, _ in scored_indices[:top_n]]
    except Exception as e:
        print(f"Error during reranking: {e}")

        # Fallback to top N unranked docs if reranking fails
        state["top_docs"] = docs[:5] 
        state["top_metadatas"] = metadatas[:5]
        if "answer" not in state:
            state["answer"] = "Error: Could not rerank documents."


    print(f"Reranked. Top {len(state.get('top_docs',[]))} documents selected.")

    # Print top reranked documents for debugging or logging purposes
    print("Top reranked documents:")
    for i, doc in enumerate(state.get("top_docs", [])):
        print(f"[Document {i + 1}]: <{doc[:200]}>")  # Print the first 200 characters of each document
    return state

def generate(state: OverallState) -> OverallState:
    if llm is None:
        print("Error: LLM not initialized.")
        # Preserve previous error/answer if any, or set a new one
        state["answer"] = state.get("answer", "Error: LLM service not available.") 
        return state

    # If a previous step set an answer (error or unanswerable), don't overwrite it
    if "answer" in state and (state["answer"] == "unanswerable" or "Error:" in state["answer"]):
        print(f"Skipping generation due to prior state: {state.get('answer')}")
        # Ensure top_docs and top_metadatas are passed through if they exist
        state["top_docs"] = state.get("top_docs", [])
        state["top_metadatas"] = state.get("top_metadatas", [])
        return state


    print("Generating answer...")
    if not state.get("top_docs"):
        print("No documents to generate answer from after reranking. Replying 'unanswerable'.")
        state["answer"] = "unanswerable"
        return state

    ctx = "\\n\\n".join(state["top_docs"])  # Qasper testing styled prompt
    prompt = f'''Prompt:Answer based on context below If you don't know the answer, say 'unanswerable'.
    If it is possible, Find the answer in the given context and use the corresponding sentence as it is.
    It shouldn't be too short answer type and reply in line, except 'unanswerable'
    If the question is a yes/no question, the answer starts with 'yes' or 'no'.

    Context:
    {ctx}

    Question: {state['question']}

    Answer:'''

    try:
        response = llm.invoke(prompt)
        state["answer"] = response.content.strip()
    except Exception as e:
        print(f"Error during LLM invocation: {e}")
        state["answer"] = "Error: Could not generate answer using LLM."

    print("Answer generated.")
    return state

# Graph Compilation
rag_pipeline = None
try:
    builder = StateGraph(state_schema=OverallState, input=InputState, output=OutputState)

    builder.add_node("retrieve", retrieve)
    builder.add_node("rerank", rerank)
    builder.add_node("generate", generate)

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "generate")
    builder.set_finish_point("generate") # The 'generate' node is the end

    rag_pipeline = builder.compile()
    print("LangGraph RAG pipeline compiled.")
except Exception as e:
    print(f"Error compiling LangGraph pipeline: {e}")
    rag_pipeline = None

# 4. FastAPI Endpoint for Processing Queries
@app.post("/process_query", response_model=AnswerResponse)
async def process_query_endpoint(request: QueryRequest):
    print(f"Received query for PDF: {request.pdf_filename}, Question: {request.question[:50]}...")
    
    # Check if essential components are initialized
    if not all([encoder, llm, rag_pipeline]): # ce_reranker is optional now
         error_msg = "Error: Backend services (encoder, LLM, or pipeline) not fully initialized. Cannot process query."
         print(error_msg)
         return AnswerResponse(ai_answer=error_msg)

    try:
        # check pdf_filename again
        pipeline_input = {"pdf_filename": request.pdf_filename, "question": request.question}
        
        result = rag_pipeline.invoke(pipeline_input)
        
        ai_ans = result.get("answer", "Error: No answer field in pipeline output.")
        # top_docs_result = result.get("top_docs", [])
        return AnswerResponse(ai_answer=ai_ans) #, top_docs=top_docs_result)

    except Exception as e:
        print(f"Error during pipeline invocation for {request.pdf_filename}: {e}")
        import traceback
        traceback.print_exc()
        return AnswerResponse(ai_answer=f"An error occurred during processing: {str(e)}")

# How to run FASTAPI app: 
# 1. Ensure .env file with HF_TOKEN and GOOGLE_API_KEY is in the LangchainTest/Final/ directory.
# 2. Install required packages: pip install fastapi uvicorn python-dotenv huggingface_hub chromadb sentence-transformers langchain_google_genai PyMuPDF langchain python-multipart protobuf==3.20.3
# 3. Run by `uvicorn [sourcefile_directory].main:app --reload --port 8000`
# 4. Upload a PDF : `/upload_pdf/` endpoint.
# 5. Query : `/process_query` endpoint with the correct `[filename].pdf`.

# POST PDF file : curl -X POST -F "file=@[filepath/filename.pdf]" http://localhost:8000/upload_pdf/
# POST Query    : curl -X POST -H "Content-Type: application/json" -d "{\"pdf_filename\": \"[filename.pdf]\", \"question\": \"What is the main topic of this document?\"}" http://localhost:8000/process_query
