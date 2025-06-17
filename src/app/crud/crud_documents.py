from fastcrud import FastCRUD

from ..models.document import Document
from ..schemas.document import DocumentCreate, DocumentRead, DocumentCreateInternal, DocumentUpdate

CRUDDocument = FastCRUD[Document, DocumentCreate, DocumentUpdate, DocumentCreateInternal, DocumentRead]
crud_documents = CRUDDocument(Document)

