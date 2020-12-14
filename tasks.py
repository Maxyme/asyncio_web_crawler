"""Tasks for the api"""
import multiprocessing

from invoke import task


@task
def start(context, num_workers=None, log_level="info"):
    """Start the api with the number of workers"""
    if num_workers is None:
        # Todo: uncomment when using a shared db between uvicorn processes
        # https://docs.gunicorn.org/en/latest/design.html#how-many-workers
        num_workers = multiprocessing.cpu_count() * 2 + 1
    context.run(
        f"uvicorn main:app --host=0.0.0.0 --workers={num_workers} --log-level={log_level}"
    )


@task
def format(context):
    """Code formatting using black"""
    context.run("black .")
