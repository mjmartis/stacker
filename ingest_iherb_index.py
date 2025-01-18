import time
import asyncio

from bs4 import BeautifulSoup

import scraper

PAGE_COUNT = 536
BATCH_SIZE = 5
REQ_THROTTLE = 1
INDEX_URL = 'http://au.iherb.com/c/supplements?p='

LINKS_FILE = 'links.txt'
ERROR_FILE = 'failed.txt'
PREV_ERROR_FILE = 'failed_1.txt'


def extract_product_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return [a['href'] for a in soup.find_all('a', class_='product-link', href=True)]


async def get_page(j, url):
    # Stagger requests within the batch.
    wait = (j % BATCH_SIZE) * REQ_THROTTLE
    await asyncio.sleep(wait)

    print(f'Fetching URL {url}')
    status, text = await scraper.get(url)
    print(f'Fetched URL {url} with response code {status}')
    return url, status, text


async def process_index(urls, process_fn, error_fn):
    link_count = len(urls)
    links = []
    for b, i in enumerate(range(0, link_count, BATCH_SIZE)):
        print(f'Batch {b+1} started')
        tasks = [get_page(j, urls[j]) for j in range(
            i, min(link_count, i + BATCH_SIZE))]

        # Process each page and extract product links
        for url, status, text in await asyncio.gather(*tasks):
            if status == 200:
                await process_fn(extract_product_links(text), url)
            else:
                await error_fn(url)

        print(f'Batch {b+1} finished')

    return links


async def save_links(links_file, links, url):
    print(f'Writing {len(links)} links from {url}')
    links_file.write('\n'.join(links))
    links_file.write('\n')
    links_file.flush()


async def save_error_url(error_file, url):
    error_file.write(f'{url}\n')
    error_file.flush()


async def main():
    urls = [f'{INDEX_URL}{j}' for j in range(1, PAGE_COUNT + 1)]
    #urls = [l.strip() for l in open(PREV_ERROR_FILE, 'r').readlines()]

    with open(LINKS_FILE, 'a') as links_file:
        with open(ERROR_FILE, 'a') as error_file:
            def process_fn(ls, u): return save_links(links_file, ls, u)
            def error_fn(u): return save_error_url(error_file, u)
            await process_index(urls, process_fn, error_fn)

if __name__ == '__main__':
    asyncio.run(main())
