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

set positional-arguments

test *args='':
  bash -c 'while (( "$#" )); do echo - $1; shift; done' -- "$@"