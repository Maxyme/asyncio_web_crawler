"""App entrypoint"""
import asyncio

from uuid import UUID

import edgedb
import structlog
from sanic import Sanic, json as json_response
from sanic.exceptions import NotFound, SanicException, BadRequest
from structlog import configure
from structlog.threadlocal import merge_threadlocal_context

from logic import crawl_website_workers
import logging

import json
configure(
    processors=[merge_threadlocal_context, structlog.processors.KeyValueRenderer()]
)
logger = structlog.get_logger()

app = Sanic("Crawler")
logging.basicConfig(level=logging.INFO)

import generated_async_edgeql as db_queries

client = edgedb.create_async_client()

#JobResult = db_queries.GetJobByIdResult

# @app.listener("before_server_start")
# async def setup_db(app):
#     #await database.connect()
#     await create_tables()


@app.listener("after_server_stop")
async def shutdown(app):
    await client.aclose()
    # await database.disconnect()


@app.route("/", methods=["GET"])
async def get_job(request):
    """Get all jobs"""
    jobs = await db_queries.get_jobs(client)
    job_ids = [str(job.id) for job in jobs]
    # todo serialize all properties
    return json_response(job_ids)


# todo: use sanic routing rules to extract query args

@app.route("/", methods=["POST"])
async def create_job(request):
    """Create a job to crawl a list of urls for images. Schedules an asyncio task for running"""
    threads = int(request.json["threads"])
    urls = request.json["urls"]
    job = await db_queries.create_job(client, threads=threads, in_progress=True, completed=False, input_urls=json.dumps(urls), image_urls=json.dumps([]))

    # create a task to crawl the given urls, note the task will be added to the event loop automatically
    # todo: save job and return id here
    asyncio.create_task(crawl_website_workers(urls, job.id, threads))
    #
    # await add_job(database, job_id, urls, threads)

    return json_response({"job_id": str(job.id), "urls": urls, "threads": threads})


# todo: use sanic routing rules to extract query args


@app.route("/result")
async def job_results(request):
    """Return the job results"""
    job_id = request.args["job_id"][0]
    job = await db_queries.get_job_by_id(client, id=job_id)
    if job is None:
        raise NotFound(f"Job id: {job_id} does not exist.")
    return json_response({"image_urls": job.image_urls})


@app.route("/status")
async def job_status(request):
    """Return the job status"""
    job_id = request.args["job_id"][0]
    job = await db_queries.get_job_by_id(client, id=job_id)
    if job is None:
        raise NotFound(f"Job id: {job_id} does not exist.")
    return json_response({"completed": job.completed, "in_progress": job.in_progress})
