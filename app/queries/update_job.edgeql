update Job
filter Job.id = <uuid>$id
set {
    image_urls := <json>$image_urls
};