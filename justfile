format:
    black .
    ruff . --fix

lint:
    black . --check
    ruff .
    mypy .

num_workers := "2"
log_level := "info"
start:
    uvicorn main:app --host=0.0.0.0 --workers={{num_workers}} --log-level={{log_level}}

make-migrations:
    edgedb migration create

migrate:
    edgedb migrate

generate-queries:
    cd app && edgedb-py --file

create-db-instance:
    edgedb project init

destroy-db-instance:
    edgedb instance destroy -I asyncio_web_crawler --force

set positional-arguments

test *args='':
  bash -c 'while (( "$#" )); do echo - $1; shift; done' -- "$@"