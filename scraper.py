import asyncio
import time
import random
import aiohttp
import os

__all__ = ['get', 'process_batches']

SCRAPE_URL = 'https://api.scrapfly.io/scrape'
REQ_THROTTLE_JITTER_SEC = 0.5


def json_lookup(json, keys):
  if keys == []:
    return json
  if keys[0] not in json:
    return None
  return json_lookup(json[keys[0]], keys[1:])


async def get(url):
  params = {
      'key': os.environ['SCRAPER_KEY'],
      'asp': 'true',
      'url': url,
  }
  async with aiohttp.ClientSession() as session:
    async with session.get(SCRAPE_URL, params=params) as response:
      json = await response.json()

      body = json_lookup(json, ['result', 'content'])
      status_code = json_lookup(json, ['result', 'status_code'])
      return status_code or 500, body


async def get_batch_page(batch_size, req_throttle_sec, page_index, url):
  # Stagger requests within the batch.
  wait = (page_index % batch_size + 1) * req_throttle_sec + random.uniform(0, REQ_THROTTLE_JITTER_SEC)
  await asyncio.sleep(wait)

  print(f'Fetching URL {url}')
  start_time = time.time()
  status, body = await get(url)
  end_time = time.time()
  print(f'Fetched URL {url} with response code {status} ({end_time - start_time}s)')
  return url, status, body


async def process_batches(batch_size, req_throttle_sec, urls, process_fn, error_fn):
  urls_count = len(urls)
  for b, i in enumerate(range(0, urls_count, batch_size)):
    print(f'Batch {b+1} started')
    tasks = [get_batch_page(batch_size, req_throttle_sec, j, urls[j])
             for j in range(i, min(urls_count, i + batch_size))]

    for url, status, body in await asyncio.gather(*tasks):
      if status == 200:
        await process_fn(body, url)
      else:
        await error_fn(url)

    print(f'Batch {b+1} finished')
