"""
FRIDAY OS - ChromaDB Provider.

Wraps the ChromaDB client to provide semantic vector storage and retrieval.
Operates asynchronously using `asyncio.to_thread` since the local persistent
client is primarily synchronous.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import chromadb  # type: ignore
from chromadb.config import Settings  # type: ignore

from backend.config import get_settings
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaProvider:
    """Provides semantic memory storage using ChromaDB."""

    def __init__(self, collection_name: str = "friday_memories") -> None:
        self.settings = get_settings()

        # Default local storage path for ChromaDB
        self.persist_directory = Path(self.settings.data_dir) / "chroma"
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize the synchronous persistent client
        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            # Using the default sentence-transformers embedding function
            # built into ChromaDB for local, offline embeddings.
        )
        logger.info("chroma_provider_initialized", collection=collection_name)

    async def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add or update a document in the vector store."""
        try:
            await asyncio.to_thread(
                self._collection.upsert,
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id],
            )
            logger.debug("chroma_document_added", doc_id=doc_id)
        except Exception as exc:
            logger.error("chroma_add_failed", doc_id=doc_id, error=str(exc))
            raise DatabaseError(
                message=f"Failed to add document to ChromaDB: {exc}",
                error_code="CHROMA_ADD_ERROR",
                details={"doc_id": doc_id, "error": str(exc)},
            ) from exc

    async def search_documents(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the vector store for semantically similar documents.

        Args:
            query: The search text.
            n_results: Number of results to return.
            where: Optional metadata filter (e.g., {"user_id": "123"}).

        Returns:
            A list of dictionaries containing 'id', 'document', 'metadata', and 'distance'.
        """
        try:
            results = await asyncio.to_thread(
                self._collection.query,
                query_texts=[query],
                n_results=n_results,
                where=where,
            )

            # Reformat Chroma's columnar response into a list of dicts
            formatted_results = []
            if results["ids"] and len(results["ids"]) > 0:
                ids = results["ids"][0]
                docs = results["documents"][0] if results["documents"] else []
                metas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []

                for i in range(len(ids)):
                    formatted_results.append(
                        {
                            "id": ids[i],
                            "document": docs[i] if i < len(docs) else "",
                            "metadata": metas[i] if i < len(metas) else {},
                            "distance": distances[i] if distances and i < len(distances) else 0.0,
                        }
                    )

            return formatted_results
        except Exception as exc:
            logger.error("chroma_search_failed", query=query, error=str(exc))
            raise DatabaseError(
                message=f"Failed to search ChromaDB: {exc}",
                error_code="CHROMA_SEARCH_ERROR",
                details={"query": query, "error": str(exc)},
            ) from exc

    async def delete_document(self, doc_id: str) -> None:
        """Delete a document from the vector store."""
        try:
            await asyncio.to_thread(
                self._collection.delete,
                ids=[doc_id],
            )
            logger.debug("chroma_document_deleted", doc_id=doc_id)
        except Exception as exc:
            logger.error("chroma_delete_failed", doc_id=doc_id, error=str(exc))
            raise DatabaseError(
                message=f"Failed to delete document from ChromaDB: {exc}",
                error_code="CHROMA_DELETE_ERROR",
                details={"doc_id": doc_id, "error": str(exc)},
            ) from exc

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the ChromaDB connection."""
        try:
            # A simple heartbeat command
            heartbeat = await asyncio.to_thread(self._client.heartbeat)
            return {
                "status": "ok",
                "provider": "chromadb",
                "heartbeat": heartbeat,
                "collection": self.collection_name,
            }
        except Exception as exc:
            return {
                "status": "error",
                "provider": "chromadb",
                "details": str(exc),
            }


# Global instance
chroma_provider = ChromaProvider()
