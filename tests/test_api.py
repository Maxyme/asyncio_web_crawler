"""Api tests"""
from time import sleep
from typing import AsyncGenerator

from httpx import AsyncClient
from pytest import fixture, mark
from main import app


@fixture
async def client() -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@mark.asyncio
async def test_root(client: AsyncClient):
    post_data = {
        "urls": ["https://blog.luizirber.org/2018/08/23/sourmash-rust/"],
        "threads": 1,
    }
    result = await client.post("/", json=post_data)
    for param in ["job_id", "threads", "urls"]:
        assert param in result.json()

    job_id = result.json()["job_id"]

    # query job while not completed
    job_finished = False
    while not job_finished:
        result = await client.get(f"/status/{job_id}")
        if result.json()["in_progress"] > 0:
            sleep(2)
        else:
            job_finished = True

    for param in ["in_progress", "completed"]:
        assert param in result.json()

    # check the final results
    result = await client.get(f"/result/{job_id}")
    assert result.json()
