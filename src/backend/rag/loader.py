from langchain_community.document_loaders import PyMuPDFLoader
from pathlib import Path

def load_pdf(path: str):
    """PDF 파일을 LangChain 문서 객체로 로드"""
    if not Path(path).exists():
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {path}")
    
    loader = PyMuPDFLoader(path)
    documents = loader.load()
    return documents

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List

def split_documents(documents: List[Document], chunk_size: int = 500, chunk_overlap: int = 100):
    """문서를 chunk로 분할"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(documents)