from typing import List, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Job(BaseModel):
    """Model to store a job details"""

    id: UUID = Field(default_factory=uuid4)
    threads: int
    input_urls: List[str]
    in_progress: int
    completed: int = 0
    image_urls: Dict[str, List[str]] = {}


class Task(BaseModel):
    """Model to store task details"""

    job_id: UUID
    main_url: str
    current_url: str
    get_sub_urls: bool
