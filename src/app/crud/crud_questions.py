"""CRUD operations for questions."""

from fastcrud import FastCRUD

from ..models.question import Question
from ..schemas.question import QuestionCreateInternal, QuestionDelete, QuestionUpdate, QuestionUpdateInternal

CRUDQuestion = FastCRUD[Question, QuestionCreateInternal, QuestionUpdate, QuestionUpdateInternal, QuestionDelete]
crud_questions = CRUDQuestion(Question)
