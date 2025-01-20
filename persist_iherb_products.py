import asyncio
import os
from urllib.parse import urlparse

import bs4
from scraper import process_batches

BATCH_SIZE = 4

LINKS_FILE = 'index_links.txt'
ERROR_FILE = 'product_failed.txt'
DEST_DIR = '/mnt/d/Dev/iherb-products'

USELESS_ELEMS = ['style', 'script', 'header', 'svg', 'head', 'link', 'meta']


async def save_error_url(error_file, url):
  error_file.write(f'{url}\n')
  error_file.flush()


async def save_product_html(error_file, html_dir, html, url):
  filename = f'{"-".join(urlparse(url).path.split("/")[-2:])}.html'
  path = os.path.join(html_dir, filename)

  soup = bs4.BeautifulSoup(html, 'html.parser')

  body = soup.find('body')
  if not body:
    await save_error_url(error_file, url)
    return

  # Remove useless large elements.
  for element in body.find_all(USELESS_ELEMS):
    element.decompose()

  pretty = soup.prettify()
  size_kb = len(pretty.encode('utf-8')) // 1024
  print(f'Saving {filename} of size {size_kb}KB')
  with open(path, 'w') as f:
    f.write(pretty)


async def main():
  with open(LINKS_FILE, 'r') as links_file, open(ERROR_FILE, 'a') as error_file:
    urls = [l.strip() for l in links_file.readlines()]

    def process_fn(b, u): return save_product_html(error_file, DEST_DIR, b, u)
    def error_fn(u): return save_error_url(error_file, u)
    await process_batches(BATCH_SIZE, urls, process_fn, error_fn)

asyncio.run(main())
