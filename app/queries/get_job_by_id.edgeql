select Job {id, threads, in_progress, completed, input_urls, image_urls, created_at}
filter Job.id = <uuid>$id
