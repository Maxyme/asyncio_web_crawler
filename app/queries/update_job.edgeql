update Job
filter Job.id = <uuid>$id
set {
    status := <StatusType>$status,
    image_urls := <array<str>>$image_urls
};