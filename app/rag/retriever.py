import os
from functools import lru_cache

from app.config import settings

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def build_index():
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import CharacterTextSplitter

    if not os.path.exists(settings.kb_path):
        raise FileNotFoundError(f"Knowledge base PDF not found at {settings.kb_path}. Put it in knowledge_base/.")
    pages = PyPDFLoader(settings.kb_path).load()
    chunks = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(pages)
    db = FAISS.from_documents(chunks, _embeddings())
    os.makedirs(settings.index_dir, exist_ok=True)
    db.save_local(settings.index_dir)
    return db


@lru_cache(maxsize=1)
def get_vectordb():
    from langchain_community.vectorstores import FAISS
    if os.path.isdir(settings.index_dir):
        return FAISS.load_local(settings.index_dir, _embeddings(), allow_dangerous_deserialization=True)
    return build_index()


def retrieve_knowledge(user_input, k=3):
    query = (f"Marketing strategy for a {user_input.campaign_goal.value} campaign "
             f"targeting {user_input.target_audience} with a {user_input.brand_tone.value} brand tone.")
    return get_vectordb().similarity_search(query, k=k)


if __name__ == "__main__":
    build_index()
    print("FAISS index built.")
