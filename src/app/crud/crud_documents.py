"""CRUD operations for documents."""

from fastcrud import FastCRUD

from ..models.document import Document
from ..schemas.document import DocumentCreateInternal, DocumentDelete, DocumentUpdate, DocumentUpdateInternal

CRUDDocument = FastCRUD[Document, DocumentCreateInternal, DocumentUpdate, DocumentUpdateInternal, DocumentDelete]
crud_documents = CRUDDocument(Document)
