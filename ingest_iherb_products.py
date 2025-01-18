import asyncio

import scraper

async def main():
  _, text = await scraper.get('https://au.iherb.com/pr/california-gold-nutrition-collagenup-hydrolyzed-marine-collagen-peptides-with-hyaluronic-acid-and-vitamin-c-unflavored-7-26-oz-206-g/64903')
  open('TEST', 'w').write(text)

asyncio.run(main())
