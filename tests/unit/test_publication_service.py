import pytest
from unittest.mock import MagicMock
from app.services.publication_service import PublicationService


@pytest.fixture
def mock_repo():
    return MagicMock()


def test_search_publications_delegates_to_repository(mock_repo):
    """Test that search_publications passes the filters through to the repo."""
    mock_repo.search_publications.return_value = ([], None)

    service = PublicationService(mock_repo)
    result = service.search_publications(query="deep", year=2024, page=2)

    # The service injects author_id=None when not provided
    mock_repo.search_publications.assert_called_once_with(
        query="deep", year=2024, page=2, author_id=None
    )
    assert result == ([], None)


def test_search_publications_with_empty_filters(mock_repo):
    """Test that empty search passes through defaults."""
    mock_repo.search_publications.return_value = ([], None)

    service = PublicationService(mock_repo)
    service.search_publications(query="", year=None, page=1)

    mock_repo.search_publications.assert_called_once_with(
        query="", year=None, page=1, author_id=None
    )


def test_search_publications_with_author_id(mock_repo):
    """Test that author_id is forwarded to the repo."""
    mock_repo.search_publications.return_value = ([], None)

    service = PublicationService(mock_repo)
    service.search_publications(query="", year=None, page=1, author_id=7)

    mock_repo.search_publications.assert_called_once_with(
        query="", year=None, page=1, author_id=7
    )


def test_get_author_graph_delegates_to_repository(mock_repo):
    """Test that the author graph query delegates to the repository sources."""
    # The repo returns a TUPLE: (authors, publications)
    mock_repo.get_author_graph_sources.return_value = ([], [])

    service = PublicationService(mock_repo)
    result = service.get_author_graph(publication_id=None, author_query="")

    mock_repo.get_author_graph_sources.assert_called_once()
    # Empty sources mean empty nodes and edges
    assert result.nodes == []
    assert result.edges == []
    assert result.highlighted_author_count == 0