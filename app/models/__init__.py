"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.publication import Author, Authored, Citation, Publication, Publisher

__all__ = ["Author", "Authored", "Citation", "Publication", "Publisher", "User"]
