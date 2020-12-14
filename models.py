from typing import List, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class InputJob(BaseModel):
    """InputJob model, used as input in the /create_job route"""

    threads: int = 1
    urls: List[str]


class ReturnJob(BaseModel):
    """ReturnJob model, used as output in the /create_job route"""

    job_id: UUID
    threads: int
    urls: List[str]


class Job(BaseModel):
    """Model to store a job details"""

    id: UUID = Field(default_factory=uuid4)
    threads: int
    input_urls: List[str]
    in_progress: int
    completed: int = 0
    image_urls: Dict[str, List[str]] = {}


class Status(BaseModel):
    """Status model, used in the /status route"""

    completed: int
    in_progress: int


class Result(BaseModel):
    """Result model, used in the /result route"""

    image_urls: Dict[str, List[str]]
