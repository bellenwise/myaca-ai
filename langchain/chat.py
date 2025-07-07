import os
from dotenv import load_dotenv
import pinecone
import openai
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.embeddings import OpenAIEmbeddings
from langchain import hub
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore

# 환경변수 로드
load_dotenv()

# API 키 로딩
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Pinecone 초기화
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


def embed(docs: list[str]) -> list[list[float]]:
    res = openai.embeddings.create(
        input=docs,
        model="text-embedding-3-small"
    )
    doc_embeds = [r.embedding for r in res.data]
    return doc_embeds


# Query
def queryFromPc(query: str, namespace: str):
    x = embed([query])

    results = index.query(
        namespace="math",
        vector=x[0],
        top_k=3,
        include_values=False,
        include_metadata=True
    )
    return results


llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.0
)
retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")

# 챗봇에게 역할 부여
retrieval_qa_chat_prompt.messages[0].prompt.template = "너는 친절한 선생님이야. 다음 내용을 바탕으로 질문에 답해줘.\n\n{context}"
combine_docs_chain = create_stuff_documents_chain(
    llm, retrieval_qa_chat_prompt
)


def queryWithContext(query: str, namespace: str):
    """
    주어진 쿼리를 사용하여 Pinecone에서 유사한 문서를 검색하고, 해당 문서들을 기반으로 답변을 생성합니다.

    Args:
        query (str): 사용자가 입력한 질문.
        namespace (str): Pinecone 네임스페이스.

    Returns:
        dict: 생성된 답변 객체.
    """
    vector_store = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=OpenAIEmbeddings(),
        namespace=namespace,
    )
    searchResult = vector_store.similarity_search(query)
    retriever = vector_store.as_retriever(search_result=searchResult)
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
    answer = retrieval_chain.invoke({"input": query})
    return answer


def savePinecone(id: str, content: str, namespace: str):
    """
    주어진 ID와 내용을 Pinecone에 저장합니다.

    Args:
        id (str): 문서의 고유 ID.
        content (str): 저장할 문서 내용.
        namespace (str): Pinecone 네임스페이스.

    Returns:
        None
    """
    data = [{"id": id, "text": content}]
    doc_embeds = embed([d["text"] for d in data])

    vectors = []
    for d, e in zip(data, doc_embeds):
        vectors.append({
            "id": d['id'],
            "values": e,
            "metadata": {'text': d['text']}
        })

    index.upsert(
        vectors=vectors,
        namespace=namespace
    )


# print(retrieval_qa_chat_prompt)
answer = queryWithContext("일차방정식이 뭐야?", namespace="math")
print(answer['answer'])
# print("\nContext used:\n\n", answer['context'])

# savePinecone("vec7", "일차방정식과 이차방정식은 다항식입니다. 일차방정식은 ax + b = 0 형태로 표현되며, 이차방정식은 ax^2 + bx + c = 0 형태로 표현됩니다.", namespace="math")
