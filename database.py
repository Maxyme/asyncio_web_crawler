"""Database queries"""
from uuid import UUID

from databases import Database
import json
from models import Job

database = Database("sqlite:///example.db")


async def create_tables(database: Database):
    """Create job table"""
    query = """
    CREATE TABLE IF NOT EXISTS Jobs (
    id VARCHAR(36) PRIMARY KEY, 
    threads INTEGER, 
    in_progress INTEGER,
    completed INTEGER,
    input_urls JSON, 
    image_urls JSON)"""
    await database.execute(query=query)


async def add_job(database: Database, job: Job):
    """Create a job"""
    query = """
    INSERT INTO Jobs(id, threads, in_progress, completed, input_urls, image_urls) 
    VALUES 
    (:id, :threads, :in_progress, :completed, :input_urls, :image_urls)
    """
    values = {
        "id": str(job.id),
        "threads": job.threads,
        "in_progress": job.in_progress,
        "completed": job.completed,
        "input_urls": json.dumps(job.input_urls),
        "image_urls": json.dumps(job.image_urls),
    }
    await database.execute(query=query, values=values)


async def update_job(database: Database, job: Job):
    """Update a job. Increment the completed and in progress counters automatically"""
    query = """
    UPDATE Jobs
    SET in_progress = in_progress - 1, completed = completed + 1, image_urls = :image_urls
    WHERE id = :id; 
    """

    values = {"image_urls": json.dumps(job.image_urls), "id": str(job.id)}
    await database.execute(query=query, values=values)


async def retrieve_job(database: Database, job_id: UUID) -> Job:
    """Retrieve a job"""
    query = "SELECT * FROM Jobs WHERE id = :id"
    result = await database.fetch_one(query=query, values={"id": str(job_id)})
    if result is None:
        raise ValueError
    return Job(
        id=result[0],
        threads=result[1],
        in_progress=result[2],
        completed=result[3],
        input_urls=json.loads(result[4]),
        image_urls=json.loads(result[5]),
    )
