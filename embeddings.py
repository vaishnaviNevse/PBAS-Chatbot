from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = Chroma(
    persist_directory="./chroma_rules",
    embedding_function=embedding_model
)

def semantic_rule_search(query):
    docs = vectorstore.similarity_search(query, k=3)
    return [doc.page_content for doc in docs]
