import asyncio
import os
import random
from urllib.parse import urlparse

import bs4
from scraper import process_batches

BATCH_SIZE = 1
REQ_THROTTLE_SEC = 5
EPOCH_SIZE = 75

LINKS_FILE = 'index_links.txt'
SUCCESS_FILE = 'product_success.txt'
ERROR_FILE = 'product_failed.txt'
LOCK_FILE = 'product.lock'
DEST_DIR = '/mnt/d/Dev/iherb-products'

URL_DISPLAY_COUNT = 2

USELESS_ELEMS = ['style', 'script', 'header', 'svg', 'head', 'link', 'meta']


async def save_error_url(error_file, url):
  error_file.write(f'{url}\n')
  error_file.flush()


async def save_product_html(error_file, html_dir, html, url):
  # Convert final slash in URL to a dash.
  filename = f'{"-".join(urlparse(url).path.split("/")[-2:])}.html'

  soup = bs4.BeautifulSoup(html, 'html.parser')

  body = soup.find('body')
  if not body:
    await save_error_url(error_file, url)
    return

  # Remove useless large elements.
  for element in body.find_all(USELESS_ELEMS):
    element.decompose()

  # Save HTML to disk.
  pretty = soup.prettify()
  size_kb = len(pretty.encode('utf-8')) // 1024
  path = os.path.join(html_dir, filename)
  print(f'Saving {filename} of size {size_kb}KB')
  with open(path, 'w') as f:
    f.write(pretty)


def subtract_list(list_a, list_b):
  '''
  Walk through sorted lists and take entries that appear in the first but not the second.
  '''

  list_c = []
  i, j = 0, 0
  while i < len(list_a):
    if j >= len(list_b) or list_a[i] < list_b[j]:
      list_c.append(list_a[i])
      i += 1
    elif list_a[i] > list_b[j]:
      j += 1
    else:  # list_a[i] == list_b[j]
      i += 1
      j += 1
  return list_c


async def process_product(success_file, error_file, html_dir, html, url):
  # Save HTML to disk.
  await save_product_html(error_file, html_dir, html, url)

  # Log successful URLs.
  success_file.write(f'{url}\n')
  success_file.flush()


async def main():
  # Use the existence of a known file to ensure we don't have concurrent executions.
  if os.path.exists(LOCK_FILE):
    raise Exception('Attempted concurrent executions')
  with open(LOCK_FILE, 'w') as f:
    f.write('')

  # Read successfully-crawled URLs. We use two opens (in read and append mode, resp.) to simplify file pointer
  # awkwardness.
  with open(SUCCESS_FILE, 'r') as ro_success_file:
    success_urls = sorted([l.strip() for l in ro_success_file.readlines()])

  # Collect an epoch of URLs that haven't yet succeeded.
  with open(LINKS_FILE, 'r') as links_file:
    all_urls = sorted([l.strip() for l in links_file.readlines()])
  unique_urls = subtract_list(all_urls, success_urls)
  random.shuffle(unique_urls)
  epoch_urls = unique_urls[:EPOCH_SIZE]

  # Provide a summary for user sanity checking.
  print(f'Downloading {len(epoch_urls)} URLs:')
  if len(epoch_urls) <= 2 * URL_DISPLAY_COUNT:
    print('  ', '\n  '.join(epoch_urls), sep='')
  else:
    print('  ', '\n  '.join(epoch_urls[:URL_DISPLAY_COUNT] + ['...'] + epoch_urls[-URL_DISPLAY_COUNT:]), sep='')
  exit(0)

  with open(SUCCESS_FILE, 'a') as success_file, open(ERROR_FILE, 'a') as error_file:
    def process_fn(b, u): return process_product(success_file, error_file, DEST_DIR, b, u)
    def error_fn(u): return save_error_url(error_file, u)
    await process_batches(BATCH_SIZE, REQ_THROTTLE_SEC, epoch_urls, process_fn, error_fn)

  # Allow other executions to start.
  os.remove(LOCK_FILE)

asyncio.run(main())
