"""Logical functions"""
import re
import time
from typing import List, Iterable

import structlog
from async_lru import alru_cache
from asyncio_pool import AioPool
from bs4 import BeautifulSoup
from httpx import AsyncClient, Timeout
from structlog.threadlocal import clear_threadlocal

from database import update_job, database
from models import Job

logger = structlog.get_logger()


async def callback(result, error, context):
    """Callback method for get_images_from_url to update job progress"""
    if error:
        logger.exception(error)
        exc, tb = error
        return exc
    job, url = context
    logger.info(f"job id: {job.id} completed for url: {url}")
    job.image_urls[url] = result
    await update_job(database, job)


async def crawl_website(job: Job, urls: List[str], threads: int = 1):
    """Crawl a website at a given url to return the images up to the second
    recursive level (ie, only one link deep from the page)"""
    structlog.threadlocal.bind_threadlocal(job_id=job.id)
    logger.info(f"Starting job id: {job.id}")
    start = time.time()

    # create an AioPool with the given number of threads/coroutines
    async with AioPool(size=threads) as pool:
        for url in urls:
            await pool.spawn(get_images_from_url_recursive(url), callback, (job, url))

    logger.info(f"Finished job id: {job.id} in {time.time() - start} seconds")
    clear_threadlocal()


async def get_html(url: str) -> str:
    """Retrieve the html content at the given url"""
    async with AsyncClient(verify=False) as client:
        response = await client.get(url, timeout=Timeout(3))
    return response.text


def get_subdomain(url: str):
    return "/".join(url.split("/")[:-1]) + "/"


@alru_cache(maxsize=128)
async def get_images_from_url_recursive(
    url: str, current_depth: int = 0, max_depth: int = 1
) -> List[str]:
    """Extract the images from the given url recursively up to max depth level"""
    logger.info(f"Extracting content from url: {url}. Current depth: {current_depth}")
    content = await get_html(url)
    soup = BeautifulSoup(content, "html.parser")
    subdomain = get_subdomain(url)
    sub_hrefs = find_all_urls(soup, subdomain)
    image_urls = find_all_images(soup, subdomain)
    logger.debug(
        f"{len(image_urls)} image(s) found: {image_urls} at depth: {current_depth} for url: {url}"
    )

    sub_images = []
    if len(sub_hrefs) > 0 and current_depth < max_depth:
        new_level = current_depth + 1
        for sub_href in sub_hrefs:
            images = await get_images_from_url_recursive(sub_href, new_level)
            sub_images.extend(images)

    return image_urls + sub_images


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
    """Find all urls in the given soup"""
    urls = soup.find_all("a", href=True)
    urls = set([url["href"] for url in urls if url.get("href")])
    return fix_relative_urls(urls, base_url)


def find_all_images(soup: BeautifulSoup, base_url) -> List[str]:
    """Find all image tags <img> with the filetype jpg, gif or png in the given soup. Note will exclude base64 images"""
    images = soup.select('img[src$=".jpg"], img[src$=".gif"], img[src$=".png"]')
    image_urls = set([img["src"] for img in images if img.get("src")])
    return fix_relative_urls(image_urls, base_url)


def find_all_images_regex(text: str) -> set[str]:
    """Find all images in the text, this will retrieve images that don't have a <img> tag as well"""
    return re.findall(is_image_regex, text)
