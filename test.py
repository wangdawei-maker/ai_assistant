import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import FAISS
# 任务1：写一个函数，读取文件夹所有txt文件
def load_docs(folder_path):
    # 你的代码
    documents = []
    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        return documents
    for file in os.listdir(folder_path):
        if file.endswith(".txt"):
            loader = TextLoader(os.path.join(folder_path, file), encoding="utf-8")
            documents.extend(loader.load())
            # print(documents)
          
    # 提示：os.listdir, TextLoader
    print(documents)
    return documents

# 任务2：写文档切分
def split_documents(docs):
    # 你的代码
    # chunk_size=200, overlap=50
    splitter=RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    chunks=splitter.split_documents(docs)
    return chunks

# 任务3：初始化embedding模型
def init_embeddings():
    # 你的代码
    # HuggingFaceEmbeddings
    embeddings=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",model_kwargs={'device': 'cpu'})
    return embeddings

# 任务4：创建向量库
def create_vectorstore(chunks, embeddings):
    # 你的代码
    # FAISS.from_documents
    vectorstore=FAISS.from_documents(documents=chunks, embedding=embeddings)
    return vectorstore

# 任务5：检索
def search(vectorstore, query):
    # 你的代码
    # similarity_search
    results=vectorstore.similarity_search(query)
    return results

load_docs("docs")