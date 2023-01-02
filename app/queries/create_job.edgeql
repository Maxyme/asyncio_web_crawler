select (insert Job {
    threads := <int16>$threads,
    status := <StatusType>$status,
    input_urls := <array<str>>$input_urls,
    image_urls := <array<str>>$image_urls
}) {
    id,
    created_at
};
