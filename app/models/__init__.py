"""
Models package for Bourhan Teacher AI.
Import all models and enums so that Alembic can detect them.
"""

from __future__ import annotations

from app.models.exam import Exam
from app.models.exam_result import ExamResult
from app.models.file import File, FileType
from app.models.group import Group
from app.models.homework import Homework, HomeworkStatus
from app.models.homework_submission import HomeworkSubmission, HomeworkSubmissionStatus
from app.models.option import Option
from app.models.question import Question, QuestionType
from app.models.student import Student, StudentLevel, StudentTrack

__all__ = [
    "Student",
    "StudentTrack",
    "StudentLevel",
    "Group",
    "File",
    "FileType",
    "Homework",
    "HomeworkStatus",
    "HomeworkSubmission",
    "HomeworkSubmissionStatus",
    "Exam",
    "Question",
    "QuestionType",
    "Option",
    "ExamResult",
]