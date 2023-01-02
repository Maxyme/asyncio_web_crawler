select (insert Job {
    threads := <int16>$threads,
    in_progress := <bool>$in_progress,
    completed := <bool>$completed,
    input_urls := <json>$input_urls,
    image_urls := <json>$image_urls
}) {
    id,
    created_at
};
