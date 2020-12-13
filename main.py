"""App entrypoint"""
import asyncio
import re
import time

from uuid import UUID
from typing import List

import structlog
from asyncio_pool import AioPool
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient, Timeout
from starlette.requests import Request
from structlog import configure
from structlog.threadlocal import merge_threadlocal_context

from models import Result, Status, Job, InputJob, ReturnJob
import logging

configure(
    processors=[merge_threadlocal_context, structlog.processors.KeyValueRenderer()]
)
logger = structlog.get_logger()

app = FastAPI()
logging.basicConfig(level=logging.INFO)

task_job_dict = {}

is_image_regex = re.compile(r"=?([^\"']*.(?:png|jpg|gif))", re.IGNORECASE)
is_html_link_regex = re.compile(r"http")


@app.post("/", response_model=ReturnJob)
async def create_job(request: Request, input_job: InputJob):
    """Create a job to crawl a list of urls for images. Schedules an asyncio task for running"""
    job = Job(
        threads=input_job.threads,
        input_urls=input_job.urls,
        in_progress=len(input_job.urls),
    )
    # create a task to crawl the given urls
    asyncio.create_task(
        crawl_website(job.id, input_job.urls, job.threads), name=str(job.id)
    )
    # save job to (tread-safe) dictionary, # todo: replace with mysqlite if using multiples uvicorn processes?
    task_job_dict[job.id] = job
    return_job = ReturnJob(
        threads=input_job.threads, urls=input_job.urls, job_id=job.id
    )
    return jsonable_encoder(return_job)


@app.get("/result/{job_id}", response_model=Result)
async def job_result(job_id: UUID):
    """Return the job results"""
    try:
        job = task_job_dict[job_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Job id does not exist")
    return Result(image_urls=job.image_urls)


@app.get("/status/{job_id}", response_model=Status)
async def job_status(job_id: UUID):
    """Return the job status"""
    try:
        job = task_job_dict[job_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Job id does not exist")
    return Status(completed=job.completed, in_progress=job.in_progress)


async def get_html(url: str) -> str:
    """Retrieve the html content at the given url"""
    async with AsyncClient(verify=False) as client:
        response = await client.get(url, timeout=Timeout(3))
    return response.text


async def get_images_from_url_recursive(
    url: str, current_depth: int = 0, max_depth: int = 1
) -> List[str]:
    """Extract the images from the given url recursively up to max depth level"""
    logger.info(f"Extracting content from url: {url}. Current depth: {current_depth}")
    content = await get_html(url)
    soup = BeautifulSoup(content, "html.parser")
    sub_hrefs = find_all_urls(soup)
    logger.info(f"Sub html references: {sub_hrefs}")
    image_urls = find_all_images(soup)
    logger.info(f"{len(image_urls)} sub images: {image_urls}")

    sub_images = []
    if len(sub_hrefs) > 0 and current_depth < max_depth:
        new_level = current_depth + 1
        for sub_href in sub_hrefs:
            images = await get_images_from_url_recursive(sub_href, new_level)
            sub_images.extend(images)

    return image_urls + sub_images


async def callback(res, err, ctx):
    """Callback method for get_images_from_url to update job progress"""
    if err:
        logger.exception(err)
        exc, tb = err
        return exc
    # Update job progress
    job, url = ctx
    logger.info(f"job id: {job.id} completed for url: {url}")
    job.in_progress -= 1
    job.completed += 1


async def crawl_website(
    job_id: UUID, urls: List[str], threads: int = 1, level: int = 0
):
    """Crawl a website at a given url to return the images up to the second
    recursive level (ie, only one link deep from the page)"""
    structlog.threadlocal.bind_threadlocal(job_id=job_id)
    logger.info(f"Starting job id: {job_id}")
    start = time.time()
    job = task_job_dict[job_id]
    # create an AioPool with the given number of threads/coroutines
    all_futures = []
    async with AioPool(size=threads) as pool:
        for url in urls:
            future = await pool.spawn(
                get_images_from_url_recursive(url), callback, (job, url)
            )
            all_futures.append((url, future))

    for url, future in all_futures:
        job.image_urls[url] = future.result()
    logger.info(f"Finished job id: {job_id} in {time.time() - start} seconds")


def find_all_urls(soup: BeautifulSoup) -> set[str]:
    """Find all urls in the given soup"""
    urls = soup.find_all("a", href=True)
    urls = [url["href"] for url in urls if re.match(is_html_link_regex, url["href"])]
    # remove duplicates
    return set(url.removesuffix("/") for url in urls)


def find_all_images(soup: BeautifulSoup) -> List[str]:
    """Find all image tags <img> with the filetype jpg, gif or png in the given soup"""
    img_tags = soup.find_all("img")
    return [
        img["src"] for img in img_tags if re.match(is_image_regex, img.get("src", ""))
    ]


def find_all_images_regex(text: str) -> set[str]:
    """Find all images in the text, this will retrieve images that don't have a <img> tag as well"""
    return re.findall(is_image_regex, text)
