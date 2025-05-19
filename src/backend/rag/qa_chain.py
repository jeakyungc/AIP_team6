import os
from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS

load_dotenv(dotenv_path="env/.env")  # 경로 

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "data/vectors")

def load_vectorstore(persist_path=VECTORSTORE_DIR):
    """FAISS 벡터 저장소 불러오기"""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    return FAISS.load_local(persist_path, embeddings, allow_dangerous_deserialization=True)

def get_rag_chain(k: int = 5):
    """Gemini 기반 RAG 체인 생성"""
    retriever = load_vectorstore().as_retriever(search_kwargs={"k": k})

    # List available models : to run this, must import google-generativeai(not langchain)
    # print("Available models:")
    # for m in google-generativeai.list_models():
    #     if 'generateContent' in m.supported_generation_methods:
    #         print(f"- {m.name}")

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", # free tier
        google_api_key=GOOGLE_API_KEY,
        temperature=0.0, # for deterministic output
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        verbose=True
    )
    return chain
