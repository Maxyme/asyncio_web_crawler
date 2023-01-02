select Job {id, threads, status, input_urls, image_urls, created_at}
filter Job.id = <uuid>$id
