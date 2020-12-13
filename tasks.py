"""Tasks for the api"""
import multiprocessing

from invoke import task


@task
def start(context, num_workers=None):
    """Start the api with the number of workers"""
    if num_workers is None:
        # https://docs.gunicorn.org/en/latest/design.html#how-many-workers
        workers = 1  # multiprocessing.cpu_count() * 2 + 1
    context.run(f"uvicorn main:app --host=0.0.0.0 --workers={workers}")


@task
def format(context):
    """Code formatting using black"""
    context.run("black .")
