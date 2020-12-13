"""App entrypoint"""
import asyncio

from uuid import UUID

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from structlog import configure
from structlog.threadlocal import merge_threadlocal_context

from database import create_tables, add_job, retrieve_job, database
from logic import crawl_website
from models import Result, Status, Job, InputJob, ReturnJob
import logging

configure(
    processors=[merge_threadlocal_context, structlog.processors.KeyValueRenderer()]
)
logger = structlog.get_logger()

app = FastAPI()
logging.basicConfig(level=logging.INFO)


@app.on_event("startup")
async def startup_event():
    """Create the database connection on startup"""
    await database.connect()
    await create_tables(database)


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/", response_model=ReturnJob)
async def create_job(request: Request, input_job: InputJob):
    """Create a job to crawl a list of urls for images. Schedules an asyncio task for running"""
    job = Job(
        threads=input_job.threads,
        input_urls=input_job.urls,
        in_progress=len(input_job.urls),
    )
    # create a task to crawl the given urls, note the task will be added to the event loop automatically
    asyncio.create_task(
        crawl_website(job, input_job.urls, job.threads), name=str(job.id)
    )
    # save job
    await add_job(database, job)
    return_job = ReturnJob(
        threads=input_job.threads, urls=input_job.urls, job_id=job.id
    )
    return jsonable_encoder(return_job)


@app.get("/result/{job_id}", response_model=Result)
async def job_result(job_id: UUID):
    """Return the job results"""
    try:
        job = await retrieve_job(database, job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job id does not exist")
    return Result(image_urls=job.image_urls)


@app.get("/status/{job_id}", response_model=Status)
async def job_status(job_id: UUID):
    """Return the job status"""
    try:
        job = await retrieve_job(database, job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job id does not exist")
    return Status(completed=job.completed, in_progress=job.in_progress)
