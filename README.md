# Asyncio based Web Crawler

## Development Prerequisites
- install [just](https://github.com/casey/just)
- install [poetry](https://python-poetry.org/)  
- install env: `poetry install --dev`
- start shell: `poetry shell`

## Running the tests  
`pytest .`

## Starting the webserver 
`just num_workers=4 log_level=debug start`

## Building the docker image  
`docker build . --tag crawler_test`

## Running the docker image on selected port 
`docker run -p 8080:8000 crawler_test`

## Testing the api, after it's running (via docker)
- visit localhost:8080/docs to interact with api in the browser

- or use httpie (or curl) commands directly:  
  - Create a job:  
    `http POST 'http://localhost:8080' urls:='["https://blog.luizirber.org/2018/08/23/sourmash-rust/", "https://gustedt.wordpress.com/2020/12/14/a-defer-mechanism-for-c/"]' threads=2`  
  - Check  a job's status:  
    `http 'http://localhost:8080/status/{job_id}'`  
  - Get the job's results:  
    `http 'http://localhost:8080/result/{job_id}'`  


## Todo:
- crash server on any worker error
- Add parameter for recursive depth for how deep to fetch sublinks
- use pytest sanic instead of pytest-async in tests
- add edgedb in docker-compose
- investigate adding nginx
- add svelte frontend server-side rendered
- multi-stage docker image (with distroless?)
- automate db migrations when starting with docker-compose