from loader import load_pdf, split_documents
from embbeder import embed_and_store, load_vectorstore
from qa_chain import get_rag_chain
from pathlib import Path

if __name__ == "__main__":
    # 1. PDF → chunks
    pdf_path = "data/raw/sample.pdf" 

    if not Path(pdf_path).exists():
        print(f"PDF 파일이 존재하지 않습니다: {pdf_path}")
        exit(1)

    documents = load_pdf(pdf_path)
    print(f"[INFO] PDF 문서 로드 완료: {len(documents)} 페이지")

    chunks = split_documents(documents)
    print(f"[INFO] 분할된 문서 조각 수: {len(chunks)}")

    # 첫 몇 개만 출력
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n[CHUNK {i+1}]\n{chunk.page_content[:500]}...")


    # 2. FAISS에 임베딩 저장
    vectorstore = embed_and_store(chunks)
    print(f"[INFO] 벡터 저장소 저장 완료")

    # 3. 벡터 저장소 불러오기 테스트
    loaded = load_vectorstore()
    print(f"[INFO] 저장소 로드 성공 - 저장된 벡터 수: {loaded.index.ntotal}")
    print("종료하려면 'exit' 입력")

    chain = get_rag_chain()
    chat_history = []

    while True:
        query = input("질문> ")
        if query.lower() in {"exit"}:
            break

        result = chain.invoke({"question": query, "chat_history": chat_history})
        
        answer = result["answer"]
        chat_history.append((query, result))
        print(f"\n응답>\n{answer}\n")

