# Asyncio based Web Crawler

## Running the tests  
`pytest .`

## Building the docker image  
`docker build . --tag crawler_test`

## Running the docker image on selected port 
`docker run -p 8080:8000 crawler_test`

## Testing the api, after it's running
- visit localhost:8080/docs to interact with api in the browser

- or use httpie (or curl) commands directly:  
  - Create a job:  
    `http POST 'http://localhost:8080' urls:='["https://blog.luizirber.org/2018/08/23/sourmash-rust/", "https://gustedt.wordpress.com/2020/12/14/a-defer-mechanism-for-c/"]' threads=2`  
  - Check  a job's status:  
    `http 'http://localhost:8080/status/{job_id}'`  
  - Get the job's results:  
    `http 'http://localhost:8080/result/{job_id}'`  