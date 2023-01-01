"""Logical functions"""
import asyncio
import re
import time
from typing import List, Iterable, Dict, Tuple

import structlog
from async_lru import alru_cache
from bs4 import BeautifulSoup
from httpx import AsyncClient, Timeout, ConnectTimeout, ConnectError

from database import update_job, database, retrieve_job
from models import Job, Task

logger = structlog.get_logger()


async def crawler_worker(
    task_queue, images_for_url: Dict[str, List[str]], sub_urls_counter: Dict[str, int]
):
    """Crawler worker instance. Fetches tasks from the queue and runs them"""
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
                sub_urls_counter[task.main_url] -= 1

            if sub_urls_counter[task.main_url] == 0:
                # Add the images for the main url removing duplicates
                images = list(set(images_for_url[task.main_url]))
                # todo: update job in 1 call instead
                job = await retrieve_job(database, task.job_id)
                job.image_urls[task.main_url] = images
                await update_job(database, job)

        except Exception as ex:
            logger.exception(ex)
        finally:
            task_queue.task_done()


async def crawl_website_workers(job: Job, urls: List[str], threads: int = 1):
    """Crawl a website at a given url to return the images up to the second
    recursive level (ie, only one link deep from the page)"""
    logger.info(f"Starting job id: {job.id}")
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
        task = Task(job_id=job.id, main_url=url, current_url=url, get_sub_urls=True)
        await task_queue.put(task)

    # Block until all items in the queue have been received and processed.
    await task_queue.join()

    # Close the worker tasks loops
    for worker in workers:
        worker.cancel()

    # wait on the worker to end properly
    await asyncio.gather(*workers, return_exceptions=True)

    logger.info(f"Finished job id: {job.id} in {time.time() - start} seconds")


@alru_cache(maxsize=128)
async def get_url_links(
    url: str, get_sub_href: bool = True
) -> Tuple[List[str], List[str]]:
    """Get all img links (and hrefs if get_sub_href=True)"""
    logger.info(f"Extracting content from url: {url}, get_sub_href {get_sub_href}")
    try:
        content = await get_html(url)
    except (ConnectTimeout, ConnectError):
        # todo: add retry behaviour instead
        return [], []
    soup = BeautifulSoup(content, "html.parser")
    subdomain = get_subdomain(url)
    if get_sub_href:
        sub_hrefs = find_all_urls(soup, subdomain)
    else:
        sub_hrefs = []
    image_urls = find_all_images(soup, subdomain)
    return image_urls, sub_hrefs


async def get_html(url: str) -> str:
    """Retrieve the html content at the given url"""
    async with AsyncClient(verify=False) as client:
        response = await client.get(url, timeout=Timeout(10))
    return response.text


def get_subdomain(url: str):
    return "/".join(url.split("/")[:-1]) + "/"


is_image_regex = re.compile(r"=?([^\"']*.(?:png|jpg|gif))", re.IGNORECASE)
is_http_regex = re.compile(r"^https?://")


def fix_relative_urls(urls: Iterable[str], base_url) -> List[str]:
    """Fix relative urls by adding the fool url subdomain"""
    full_urls = []
    for url in urls:
        if not re.match(is_http_regex, url):
            full_urls.append(f"{base_url.removesuffix('/')}{url}")
        else:
            full_urls.append(url)
    return full_urls


def find_all_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Find all href urls in the given soup. Note, will ignore mailto and # references"""
    urls = soup.select("a[href]:not(a[href^=mailto\:], a[href^=\#], a[href$='.pdf'])")
    urls = set([url["href"] for url in urls if url.get("href")])
    return fix_relative_urls(urls, base_url)


def find_all_images(soup: BeautifulSoup, base_url) -> List[str]:
    """Find all image tags <img> with the filetype jpg, gif or png in the given soup. Note will exclude base64 images"""
    images = soup.select('img[src$=".jpg"], img[src$=".gif"], img[src$=".png"]')
    image_urls = set([img["src"] for img in images if img.get("src")])
    return fix_relative_urls(image_urls, base_url)


def find_all_images_regex(text: str) -> List[str]:
    """Find all images in the text, this will retrieve images that don't have a <img> tag as well"""
    return re.findall(is_image_regex, text)
