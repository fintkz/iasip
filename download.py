from playwright.sync_api import sync_playwright
import os
import shutil
from urllib.parse import unquote, urljoin
from tqdm import tqdm
import requests
from concurrent.futures import ThreadPoolExecutor

def get_free_space(path):
   stats = shutil.disk_usage(path)
   return stats.free / (1024 * 1024 * 1024)

def log(msg):
   print(f"[*] {msg}")

def download_file(url, filepath):
   log(f"Starting download: {url}")
   response = requests.get(url, stream=True)
   total = int(response.headers.get('content-length', 0))
   
   with open(filepath, 'wb') as f, tqdm(
       total=total,
       unit='iB',
       unit_scale=True,
       unit_divisor=1024,
   ) as pbar:
       for data in response.iter_content(chunk_size=1024):
           size = f.write(data)
           pbar.update(size)

def download_season(season_num, max_workers=8):
   base_url = "https://archive.org/download/its_always_sunny_complete_archive/"
   save_dir = "/Users/fintkz/Movies/tv/iasip"

   with sync_playwright() as p:
       log("Launching browser")
       browser = p.chromium.launch()
       context = browser.new_context(accept_downloads=True)
       page = context.new_page()
       
       log(f"Navigating to archive.org")
       page.goto(base_url, timeout=60000)

       log(f"Looking for Season {season_num}")
       links = page.locator('td a').all()
       season_link = None
       for link in links:
           text = link.text_content()
           if text.startswith(f'Season {season_num} - '):
               season_link = link
               log(f"Found link: {text}")
               break

       if not season_link:
           log("Season not found!")
           return

       season_url = urljoin(base_url, season_link.get_attribute('href'))
       log(f"Navigating to season page: {season_url}")
       
       season_dir = f"{save_dir}/{season_num}"
       os.makedirs(season_dir, exist_ok=True)

       page.goto(season_url, timeout=60000)
       log("Scanning for video files...")
       
       files = []
       rows = page.locator('tr').all()[1:]
       for row in rows:
           cells = row.locator('td').all()
           if len(cells) < 3:
               continue
               
           link = cells[0].locator('a')
           href = link.get_attribute('href')
           if not href or not href.endswith(('.mkv', '.mp4')):
               continue

           size_text = cells[2].text_content().strip()
           if not size_text or size_text == '-':
               continue

           if 'M' in size_text:
               size_gb = float(size_text.replace('M', '')) / 1024
           elif 'G' in size_text:
               size_gb = float(size_text.replace('G', ''))
           else:
               continue

           files.append((link, size_gb))

       log(f"Found {len(files)} video files")
       total_size = sum(size for _, size in files)
       free_space = get_free_space(save_dir)
       
       print(f"\nSeason {season_num} requires {total_size:.1f}GB. You have {free_space:.1f}GB free.")
       if input("Proceed? (y/n): ").lower() != 'y':
           return

       with ThreadPoolExecutor(max_workers=max_workers) as executor:
           futures = []
           for i, (link, _) in enumerate(files, 1):
               filename = unquote(link.get_attribute('href').split('/')[-1])
               filepath = f"{season_dir}/{filename}"
               url = urljoin(season_url, link.get_attribute('href'))
               
               log(f"Queueing ({i}/{len(files)}): {filename}")
               log(f"URL: {url}")
               
               futures.append(executor.submit(download_file, url, filepath))

           log(f"All downloads queued! Using {max_workers} workers")
           for future in futures:
               future.result()  # Wait for completion

       log("All downloads complete!")
       browser.close()

if __name__ == "__main__":
   season = int(input("Which season to download (1-10)? "))
   if 1 <= season <= 10:
       download_season(season)
