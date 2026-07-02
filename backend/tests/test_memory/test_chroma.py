from unittest.mock import MagicMock, patch

import pytest

from backend.memory.chroma import ChromaProvider


@pytest.fixture
def mock_chroma():
    with patch("backend.memory.chroma.chromadb.PersistentClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_collection = MagicMock()
        mock_instance.get_or_create_collection.return_value = mock_collection
        yield mock_collection


@pytest.mark.asyncio
async def test_chroma_add_document(mock_chroma):
    provider = ChromaProvider(collection_name="test_memories")

    await provider.add_document("doc_1", "test content", {"user_id": "123"})

    mock_chroma.upsert.assert_called_once_with(
        documents=["test content"], metadatas=[{"user_id": "123"}], ids=["doc_1"]
    )


@pytest.mark.asyncio
async def test_chroma_search_documents(mock_chroma):
    provider = ChromaProvider(collection_name="test_memories")

    # Mock chroma return format
    mock_chroma.query.return_value = {
        "ids": [["doc_1", "doc_2"]],
        "documents": [["text 1", "text 2"]],
        "metadatas": [[{"user_id": "123"}, {"user_id": "123"}]],
        "distances": [[0.1, 0.5]],
    }

    results = await provider.search_documents("query", n_results=2)

    assert len(results) == 2
    assert results[0]["id"] == "doc_1"
    assert results[1]["distance"] == 0.5
