"""Debug tools"""
import asyncio

from logic import get_images_from_url_recursive


async def main():
    url = "https://varvy.com/pagespeed/wicked-fast.html"
    images = await get_images_from_url_recursive(url, max_depth=1)
    print(images)


if __name__ == "__main__":
    asyncio.run(main())
