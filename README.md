# Asyncio based Web Crawler

## Running the tests  
`pytest .`

## Building the docker image  
`docker build . --tag crawler_test`

## Running the docker image on selected port 
`docker run -p 8080:8000 crawler_test`

## Running the docker image on with a limited number of cpu (to test a single process) 
`docker run -p 8080:8000 --cpus 1 crawler_test`

