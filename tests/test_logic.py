"""Test application logic"""
from bs4 import BeautifulSoup
from pytest import mark

from logic import (
    find_all_urls,
    find_all_images,
    find_all_images_regex,
    get_html,
    get_images_from_url_recursive,
)

html = """
<html>
 <head>
  <title>
   The Dormouse's story
  </title>
 </head>
 <body>
  <p class="title">
   <b>
    The Dormouse's story
   </b>
  </p>
  <p class="story">
   Once upon a time there were three little sisters; and their names were
   <a class="sister" href="http://example.com/elsie" id="link1">
    Elsie
   </a>
   ,
   <a class="sister" href="http://example.com/lacie" id="link2">
    Lacie
   </a>
   and
   <a class="sister" href="http://example.com/tillie" id="link3">
    Tillie
   </a>
   ; and they lived at the bottom of a well.
  </p>
  
  <p><a href="https://www.ssrg.ece.vt.edu/papers/vee2019.pdf"> PDF </a></p>
  <img src="img_chania.jpg" title="Flowers in Chania" alt="Flowers in Chania"> 
  <img src="img_chania.png" title="Flowers in Chania" alt="Flowers in Chania"> 
  <img src="img_chania.gif" title="Flowers in Chania" alt="Flowers in Chania"> 
  <img src="img_chania.webp" title="Flowers in Chania" alt="Flowers in Chania"> 
  <img src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
  <p><a href="mailto:someone@example.com">Send email</a></p>
  <p><a>Send email</a></p>
  <weird images from google>
  <meta content="https://www.google.com/logos/doodles/2020/december-holidays-days-2-30-6753651837108830.3-2xa.gif" property="twitter:image">
  <p class="story">
   Lorem Ipsum
  </p>
 </body>
</html>
"""


def test_search_urls():
    """Test the search url method"""
    soup = BeautifulSoup(html, "html.parser")
    urls = find_all_urls(soup, base_url="")
    assert len(urls) == 3
    assert "http://example.com/tillie" in urls


def test_search_images_regex():
    """Test the search images method"""
    image_list = find_all_images_regex(html)
    assert len(image_list) == 4
    for filetype in [".jpg", ".png", ".gif"]:
        assert f"img_chania.{filetype}"


def test_search_images():
    """Test the search images method"""
    soup = BeautifulSoup(html, "html.parser")
    image_list = find_all_images(soup)
    assert len(image_list) == 3
    for filetype in [".jpg", ".png", ".gif"]:
        assert f"img_chania.{filetype}"


@mark.asyncio
async def test_get_html():
    """Test the get_html method"""
    url = "https://blog.luizirber.org/2018/08/23/sourmash-rust/"
    content = await get_html(url)
    assert "<!DOCTYPE html>" in content


@mark.asyncio
async def test_get_content_from_url():
    """Test get_images_from_url_recursive"""
    url = "https://google.com"
    images = await get_images_from_url_recursive(url, max_depth=0)
    assert len(images) > 0
