import aiohttp
import os


async def get(url):
    headers = { 'Accept': 'text/html', 'Accept-Encoding': 'gzip, deflate' }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=os.environ['PROXY_URL'], ssl=False, headers=headers) as response:
            return response.status, (await response.text())
