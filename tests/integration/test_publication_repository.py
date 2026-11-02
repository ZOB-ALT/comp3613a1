import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.publication import PublicationRepository
from app.repositories.user import UserRepository
from app.models.publication import Publication, Publisher, Author, Authored
from app.schemas.publication import PublicationForm
from app.schemas.user import RegularUserCreate
from app.utilities.security import encrypt_password


@pytest.fixture(name="sample_publisher")
def sample_publisher_fixture(session):
    publisher = Publisher(name="Test Publisher")
    session.add(publisher)
    session.commit()
    session.refresh(publisher)
    return publisher


@pytest.fixture(name="sample_author")
def sample_author_fixture(session):
    user_repo = UserRepository(session)
    user = user_repo.create(RegularUserCreate(
        username="pubauthor", email="pubauthor@mail.com",
        password=encrypt_password("pass"), role="regular_user",
    ))
    author = Author(
        user_id=user.id, first_name="Pub", last_name="Author",
        affiliation="Test Uni", email="pubauthor@mail.com",
    )
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


@pytest.fixture(name="sample_publication")
def sample_publication_fixture(session, sample_publisher, sample_author):
    """Create a publication using the real repository."""
    repo = PublicationRepository(session)
    form = PublicationForm(
        title="Integration Test Paper",
        abstract="An abstract for testing",
        doi="10.5555/int.test.001",
        publisher_id=sample_publisher.id,
        journal="Test Journal",
        conference="Test Conf",
        year=2024,
        keywords="test, integration",
        author_ids=[sample_author.id],
        citation_ids=[],
    )
    return repo.create_publication(form)


def test_create_and_retrieve_publication(session, sample_publication):
    """Test that a publication saves and is retrievable by ID."""
    repo = PublicationRepository(session)
    found = repo.get_by_id_with_related(sample_publication.id)
    assert found is not None
    assert found.title == "Integration Test Paper"
    assert found.doi == "10.5555/int.test.001"


def test_search_publications_by_title(session, sample_publication):
    """Test that search by title returns matching publications."""
    repo = PublicationRepository(session)
    results, pagination = repo.search_publications(
        query="Integration", year=None, page=1,
    )
    assert len(results) >= 1
    assert any("Integration" in p.title for p in results)


def test_search_publications_by_year(session, sample_publication):
    """Test that year filter narrows the results."""
    repo = PublicationRepository(session)
    results, _ = repo.search_publications(query="", year=2024, page=1)
    assert len(results) >= 1
    for p in results:
        assert p.year == 2024


def test_search_publications_no_match(session, sample_publication):
    """Test that a search with no matching results returns empty."""
    repo = PublicationRepository(session)
    results, _ = repo.search_publications(
        query="ZZZNoSuchPaperZZZ", year=None, page=1,
    )
    assert len(results) == 0


def test_publication_doi_is_unique(session, sample_publication, sample_publisher, sample_author):
    """Test that a duplicate DOI raises an IntegrityError."""
    repo = PublicationRepository(session)
    duplicate = PublicationForm(
        title="Duplicate DOI Paper",
        abstract="x",
        doi="10.5555/int.test.001",  # same as sample_publication
        publisher_id=sample_publisher.id,
        journal="x",
        conference="x",
        year=2024,
        keywords="x",
        author_ids=[sample_author.id],
        citation_ids=[],
    )
    with pytest.raises(IntegrityError):
        repo.create_publication(duplicate)