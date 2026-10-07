from app.rag.retriever import build_index

if __name__ == "__main__":
    build_index()
    print("FAISS index built.")
