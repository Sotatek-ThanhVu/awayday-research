import os
from typing import Any, List, Sequence, Tuple

from dotenv import load_dotenv
from llama_index import (Document, ServiceContext, SimpleDirectoryReader,
                         StorageContext, VectorStoreIndex)
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.embeddings import GeminiEmbedding
from llama_index.llms.utils import LLMType
from llama_index.node_parser import JSONNodeParser, get_leaf_nodes
from llama_index.schema import BaseNode
from llama_index.storage.docstore.simple_docstore import SimpleDocumentStore
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

load_dotenv()


def load_documents() -> List[Document]:
    """
    Load source documents
    """

    # loader = DatabaseReader(uri=connection_string)
    loader = SimpleDirectoryReader(
        input_files=["./documents/_event__202401120928.json"]
    )
    documents = loader.load_data(show_progress=True)
    # document = Document(text="\n\n".join([doc.get_content() for doc in documents]))S

    return documents


def build_nodes(documents: List[Document]) -> List[BaseNode]:
    """
    Parsing source documents into smaller chunks (nodes)
    """

    # node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2049, 1024, 512])
    node_parser = JSONNodeParser.from_defaults(callback_manager=callback_manager)
    nodes = node_parser.get_nodes_from_documents(
        documents=documents, show_progress=True
    )
    return nodes


def build_context(
    nodes: Sequence[BaseNode] | None,
    embed_model: Any | None,
    callback_manager: CallbackManager | None,
    llm: LLMType | None = None,
) -> Tuple[ServiceContext, StorageContext]:
    """
    Construct ServiceContext and StorageContext
    """

    service_context = ServiceContext.from_defaults(
        llm=llm, embed_model=embed_model, callback_manager=callback_manager
    )

    # docstore = SimpleDocumentStore()
    # docstore.add_documents(nodes)
    vector_store = PGVectorStore.from_params(
        host=url.host,
        port=str(url.port),
        database=url.database,
        user=url.username,
        password=url.password,
        embed_dim=768,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return service_context, storage_context


def build_index(
    nodes: List[BaseNode], context: Tuple[ServiceContext, StorageContext]
) -> VectorStoreIndex:
    """
    Construct vector index
    """

    index = VectorStoreIndex(
        # nodes=get_leaf_nodes(nodes),
        nodes=nodes,
        service_context=context[0],
        storage_context=context[1],
        show_progress=True,
    )

    return index


def main() -> None:
    documents = load_documents()
    nodes = build_nodes(documents)
    # context = build_context(nodes, embed_model, callback_manager)
    context = build_context(None, embed_model, callback_manager)
    index = build_index(nodes, context)

    index.storage_context.persist()


if __name__ == "__main__":
    connection_string = os.getenv("CONNECTION_STRING")
    url = make_url(connection_string)

    embed_model = GeminiEmbedding()
    callback_manager = CallbackManager([LlamaDebugHandler(print_trace_on_end=True)])

    main()
