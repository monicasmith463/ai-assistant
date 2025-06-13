from fastcrud import FastCRUD

from ..models.document import Document
from ..schemas.document import DocumentCreate, DocumentRead, DocumentCreateInternal

CRUDDocument = FastCRUD[Document, DocumentCreate, DocumentCreateInternal, DocumentRead]

crud_documents = CRUDDocument(Document)

