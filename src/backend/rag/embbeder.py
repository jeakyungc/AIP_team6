import os
from dotenv import load_dotenv
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS

load_dotenv(dotenv_path="env/.env")  # 경로 

# 환경 변수
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "data/vectors")


def embed_and_store(docs, persist_path=VECTORSTORE_DIR):
    """문서 임베딩 후 FAISS 벡터 저장소에 저장"""
    print(GOOGLE_API_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(persist_path)
    return vectorstore


def load_vectorstore(persist_path=VECTORSTORE_DIR):
    """FAISS 벡터 저장소 불러오기"""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    return FAISS.load_local(persist_path, embeddings, allow_dangerous_deserialization=True) 
    # .pkl 파일 역질렬화 (보안위험있음)
