# Asyncio based Web Crawler

## Running the tests  
`pytest .`

## Building the docker image  
`docker build . --tag crawler_test`

## Running the docker image on selected port 
`docker run crawler_test -p 8080:8080`

## Running the docker image on with a limited number of cpu (to test a single process) 
`docker run crawler_test -p 8080:8080 --cpus 1`

