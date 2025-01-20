import time
import asyncio

from bs4 import BeautifulSoup

from scraper import process_batches

PAGE_COUNT = 538
BATCH_SIZE = 4
INDEX_URL = 'http://au.iherb.com/c/supplements?p='

LINKS_FILE = 'index_links.txt'
ERROR_FILE = 'index_failed.txt'
PREV_ERROR_FILE = 'index_failed_1.txt'


def extract_product_links(html_content):
  soup = BeautifulSoup(html_content, 'html.parser')
  return [a['href'] for a in soup.find_all('a', class_='product-link', href=True)]


async def save_links(links_file, links, url):
  print(f'Writing {len(links)} links from {url}')
  links_file.write('\n'.join(links))
  links_file.write('\n')
  links_file.flush()


async def save_extracted_links(links_file, body, url):
  await save_links(links_file, extract_product_links(body), url)


async def save_error_url(error_file, url):
  error_file.write(f'{url}\n')
  error_file.flush()


async def main():
  urls = [f'{INDEX_URL}{j}' for j in range(1, PAGE_COUNT + 1)]
  # urls = [l.strip() for l in open(PREV_ERROR_FILE, 'r').readlines()]

  with open(LINKS_FILE, 'a') as links_file, open(ERROR_FILE, 'a') as error_file:
    def process_fn(b, u): return save_extracted_links(links_file, b, u)
    def error_fn(u): return save_error_url(error_file, u)
    await process_batches(BATCH_SIZE, urls, process_fn, error_fn)

if __name__ == '__main__':
  asyncio.run(main())
