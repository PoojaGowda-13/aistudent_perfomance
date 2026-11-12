"""
ChromaDB vector store — graceful fallback when ChromaDB is not installed.
"""
import structlog

logger = structlog.get_logger(__name__)

_client = None
_embedder = None
_chroma_available = False

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    _chroma_available = True
except ImportError:
    logger.warning("chromadb_not_installed", msg="Vector search disabled. Install chromadb for full functionality.")

try:
    from sentence_transformers import SentenceTransformer
    _st_available = True
except ImportError:
    _st_available = False


def get_chroma_client():
    global _client
    if not _chroma_available:
        return None
    if _client is None:
        from app.config import get_settings
        settings = get_settings()
        try:
            _client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        except Exception as e:
            logger.warning("chroma_init_failed", error=str(e))
            return None
    return _client


def get_embedder():
    global _embedder
    if not _st_available:
        return None
    if _embedder is None:
        try:
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            return None
    return _embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    embedder = get_embedder()
    if embedder is None:
        # Return random embeddings as fallback (semantic search disabled)
        import random
        return [[random.random() for _ in range(384)] for _ in texts]
    return embedder.encode(texts, show_progress_bar=False).tolist()


def get_collection(name: str):
    client = get_chroma_client()
    if client is None:
        return None
    return client.get_or_create_collection(name=name)


def upsert_documents(collection_name: str, documents: list[str], ids: list[str], metadatas: list[dict] = None):
    collection = get_collection(collection_name)
    if collection is None:
        return
    embeddings = embed_texts(documents)
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas or [{} for _ in documents],
    )


def query_similar(collection_name: str, query_text: str, n_results: int = 5) -> list[dict]:
    """Query vector DB for similar documents. Returns empty list if unavailable."""
    collection = get_collection(collection_name)
    if collection is None:
        return []
    try:
        query_embedding = embed_texts([query_text])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        items = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            items.append({"document": doc, "metadata": meta, "distance": dist})
        return items
    except Exception as e:
        logger.warning("chroma_query_failed", error=str(e))
        return []
