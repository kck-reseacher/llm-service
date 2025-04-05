import requests
import faiss
import fitz
import numpy as np
import time
import os
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter


def fetch_text_from_url(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()  # 텍스트만 추출


def fetch_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def fetch_texts_from_pdf_dir(pdf_dir):
    pdf_docs = []

    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(pdf_dir, filename)
            # print(f"🔍 처리 중: {file_path}")
            text = fetch_text_from_pdf(file_path)
            pdf_docs.append({
                "filename": filename,
                "text": text
            })

    return pdf_docs


def langchain_split_text(text, chunk_size=512, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)


def get_embeddings(chunks):
    return model.encode(chunks)


# 4. FAISS 벡터스토어 클래스
class FaissStore:
    def __init__(self, dim):
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []
        self.metadatas = []

    def add(self, embeddings, texts, types):
        self.index.add(np.array(embeddings).astype("float32"))
        self.texts.extend(texts)
        self.metadatas.extend(types)

    def search(self, query_embedding, top_k=5, doc_type=None):
        D, I = self.index.search(np.array([query_embedding]).astype("float32"), top_k * 3)
        results = []
        count = 0
        for idx in I[0]:
            if doc_type is None or self.metadatas[idx] == doc_type:
                results.append(self.texts[idx])
                count += 1
                if count >= top_k:
                    break
        return results

    # def search(self, query_embedding, top_k=3):
    #     D, I = self.index.search(np.array([query_embedding]).astype("float32"), top_k)
    #     return [self.texts[i] for i in I[0]]


# 5. Ollama LLM 호출
def query_ollama(context, question, model="eeve"):
    prompt = f"""너는 솔루션 매뉴얼 및 기술 자료 내용을 요약하고 질문에 답변하는 도우미야. 

    아래는 매뉴얼과 기술자료에서 수집한 컨텍스트야: 
    {context}

    위 내용을 참고해서 다음 질문에 한국어로 답해줘:

    {question}

    ※ 답변은 위 컨텍스트만을 기반으로, 추가적인 정보 없이 자연스럽게 작성해줘.
    """

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(f"http://10.10.34.20:11435/api/generate", json=payload)
    response.raise_for_status()
    return response.json()["response"].strip()


def classify_question_type_with_llm(question: str, model="eeve") -> str:
    prompt = f"""
    다음 질문이 어떤 유형의 문서를 참조해야 하는지 분류해줘: guide / tech / manual 중 하나로만 답해.
    질문: "{question}"
    답: 
    """

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(f"http://10.10.34.20:11435/api/generate", json=payload)
    response.raise_for_status()
    return response.json()["response"].strip()


if __name__ == "__main__":
    embedding_start = time.time()
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # or any embedding model

    # url = "http://10.10.34.14:8082/manual/Admin/InterMax_V5.2_Admin.html"  # 👉 분석할 HTML 페이지 URL
    # manual doc
    html_urls = [
        "http://10.10.34.14:8082/manual/Install/InterMax_V5.2_Install.html",
        "http://10.10.34.14:8082/manual/Admin/InterMax_V5.2_Admin.html",
        "http://10.10.34.14:8082/manual/Configuration/InterMax_V5.2_Configuration.html",
        "http://10.10.34.14:8082/manual/RTM/InterMax_V5.2_RTM.html",
        "http://10.10.34.14:8082/manual/PA/InterMax_V5.2_PA.html"
    ]

    pdf_path = []

    all_chunks = []
    all_embeddings = []
    all_types = []

    for url in html_urls:
        text = fetch_text_from_url(url)
        chunks = langchain_split_text(text)
        embeddings = embedding_model.encode(chunks)
        all_chunks.extend(chunks)
        all_embeddings.extend(embeddings)
        all_types.extend(["manual"] * len(chunks))

    doc_types = ["guide", "tech"]
    for doc_type in doc_types:
        pdf_dir = f"/home/kck/llm/mistral_models/rag/apm/{doc_type}"
        pdf_docs = fetch_texts_from_pdf_dir(pdf_dir)

        for doc in pdf_docs:
            chunks = langchain_split_text(doc['text'])
            embeddings = embedding_model.encode(chunks)
            all_chunks.extend(chunks)
            all_embeddings.extend(embeddings)
            all_types.extend([doc_type] * len(chunks))

    print(f"embedding elapsed: {time.time() - embedding_start:.2f}")

    vector_store_start = time.time()
    store = FaissStore(dim=384)
    store.add(all_embeddings, all_chunks, all_types)

    # question = "Platform.JS 와 관련된 설정에 대해 자세하게 설명해줘"
    question = "Performance Trend 화면에 대해 설명해줘"
    # q_type = classify_question_type_with_llm(question)
    q_type = 'manual'
    print(f"q_type: {q_type}")
    q_embedding = embedding_model.encode([question])[0]
    relevant_chunks = store.search(q_embedding, top_k=3, doc_type=q_type)

    context = "\n".join(relevant_chunks)
    print(f"vector_store elapsed: {time.time() - vector_store_start:.2f}")

    ollama_serv_start = time.time()
    answer = query_ollama(context, question)
    print(f"ollama serv elapsed: {time.time() - ollama_serv_start}")

    print("🔍 질문:", question)
    print("💬 답변:", answer)
