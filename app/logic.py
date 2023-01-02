"""Logical functions"""
import asyncio
import re
import time
from typing import List, Dict, Tuple
from urllib.parse import urljoin

# todo: import from main
import generated_async_edgeql as db_queries
import aiohttp
import edgedb
import structlog
from async_lru import alru_cache
from bs4 import BeautifulSoup

from models import Task

client = edgedb.create_async_client()

logger = structlog.get_logger()

HTTP_URL_RE = re.compile("^https?://")


async def crawler_worker(
    task_queue, images_for_url: Dict[str, List[str]], sub_urls_counter: Dict[str, int]
):
    """Crawler worker instance. Fetch tasks from the queue and runs them"""
    while True:
        try:
            task = await task_queue.get()
            image_urls, sub_hrefs = await get_url_links(
                task.current_url, task.get_sub_urls
            )

            # update the images for the main url
            images_for_url[task.main_url].extend(image_urls)

            # create other sub tasks and set the sub url counter if get_sub_urls is True
            if task.get_sub_urls:
                # create the sub urls counters:
                sub_urls_counter[task.main_url] = len(sub_hrefs)
                # add the sub urls to the task queue
                for current_url in sub_hrefs:
                    task = Task(
                        job_id=task.job_id,
                        main_url=task.main_url,
                        current_url=current_url,
                        get_sub_urls=False,
                    )
                    await task_queue.put(task)
            else:
                # decrement the sub urls counter
                sub_urls_counter[task.main_url] = 0  # -= 1

            if sub_urls_counter[task.main_url] == 0:
                # Add the images for the main url removing duplicates
                images = list(set(images_for_url[task.main_url]))
                await db_queries.update_job(
                    client,
                    id=task.job_id,
                    image_urls=images,
                    status=db_queries.Status.COMPLETED,
                )

        except Exception as ex:
            logger.exception(ex)
        finally:
            task_queue.task_done()


async def crawl_website_workers(urls: List[str], job_id, threads: int = 1):
    """Crawl a website at a given url to return the images up to the second
    recursive level (ie, only one link deep from the page)"""
    logger.info(f"Starting job id: {job_id}")
    start = time.time()

    task_queue = asyncio.Queue()

    images_for_url: Dict[str, List[str]] = {}
    sub_urls_counter = {}
    for url in urls:
        images_for_url[url] = []
        sub_urls_counter[url] = 0

    # create a number of workers equivalent to the requested threads
    workers = [
        asyncio.create_task(
            crawler_worker(task_queue, images_for_url, sub_urls_counter)
        )
        for _ in range(threads)
    ]

    # create the initial tasks for the workers from the first batch of urls
    for url in urls:
        task = Task(job_id=job_id, main_url=url, current_url=url, get_sub_urls=True)
        await task_queue.put(task)

    # Block until all items in the queue have been received and processed.
    await task_queue.join()

    # Close the worker tasks loops
    for worker in workers:
        worker.cancel()

    # wait on the worker to end properly
    await asyncio.gather(*workers, return_exceptions=True)
    logger.info(f"Finished job id: {job_id} in {time.time() - start} seconds")


@alru_cache(maxsize=128)
async def get_url_links(
    url: str, get_sub_href: bool = True
) -> Tuple[List[str], List[str]]:
    """Get all img links (and hrefs if get_sub_href=True)"""
    logger.info(f"Extracting content from url: {url}, get_sub_href {get_sub_href}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    if get_sub_href:
        sub_urls = [link["href"] for link in soup.find_all("a", attrs={"href": HTTP_URL_RE})]
    else:
        sub_urls = []

    image_urls = [
        urljoin(url, link["src"])
        for link in soup.find_all("img", attrs={"src": HTTP_URL_RE})
    ]
    return image_urls, sub_urls
