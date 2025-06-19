import requests
import time
import os, sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Configuration ---
# Be a good internet citizen: set a delay between your requests.
CRAWL_DELAY_SECONDS = 0.01
# Set a user-agent to identify your bot. Some sites block default Python user-agents.
HEADERS = {
    'User-Agent': 'MyWebsiteConverterBot/1.0 (+http://www.example.com/bot-info)'
}
# List of file extensions to ignore in links
IGNORED_EXTENSIONS = [
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4'
]

def crawl_site(start_url: str) -> list[str]:
    """
    Crawls a website starting from start_url and returns a list of unique, internal URLs.

    Args:
        start_url: The URL of the homepage to begin crawling.

    Returns:
        A sorted list of all unique URLs found on the same domain.
    """
    try:
        domain_name = urlparse(start_url).netloc
    except Exception as e:
        print(f"Error: Invalid start URL provided: {start_url}. {e}")
        return []

    queue = [start_url]
    visited_urls = set()
    unique_urls = set()

    print(f"Starting crawl at: {start_url}")
    print(f"Domain to crawl: {domain_name}")

    while queue:
        # Get the next URL from the queue
        current_url = queue.pop(0)

        # Skip if we've already processed this URL
        if current_url in visited_urls:
            continue

        #print(f"  -> Crawling: {current_url}")

        found = False
        for extra_path in EXTRA_PATHS:
          if not extra_path:
            test_url = current_url
          else:
            test_url = "%s%s" %(extra_path,
              os.path.split(current_url)[-1])
          test_url = remove_double_slash_except_at_start(test_url)

          try:
              # Add URL to our set of visited URLs
              visited_urls.add(test_url)

              # Make the HTTP request
              time.sleep(CRAWL_DELAY_SECONDS) # Respect the delay
              response = requests.get(test_url, headers=HEADERS, timeout=10)
              response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
              found = True
              unique_urls.add(test_url) # a good one
              break
          except requests.exceptions.RequestException as e:
              pass

        if not found:
              print(f"     [!] Failed to retrieve {current_url}")
              continue # Move to the next URL in the queue

        if test_url == current_url:
          print("Found: %s" %(test_url))
        else:
          print("Found: %s (was: %s)" %(test_url, current_url))
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor tags with an 'href' attribute
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Use urljoin to build an absolute URL from a relative one (e.g., from "/about" to "https://site.com/about")
            absolute_link = urljoin(start_url, href)

            # --- Filtering Logic: Decide if the link is worth adding to the queue ---

            # 1. Parse the link to analyze its components
            parsed_link = urlparse(absolute_link)

            # 2. Check if the link is on the same domain
            if parsed_link.netloc != domain_name:
                continue

            # 3. Check if it's a standard http or https link
            if parsed_link.scheme not in ['http', 'https']:
                continue

            # 4. Check if the link has an extension we want to ignore
            if any(absolute_link.lower().endswith(ext) for ext in IGNORED_EXTENSIONS):
                continue

            # 5. Clean up fragments (e.g., remove "#section" from the end of a URL)
            clean_link = parsed_link._replace(fragment="").geturl()
            clean_link = remove_double_slash_except_at_start(clean_link)
            if (clean_link.find("?") > -1 ):
              continue  # skip
            if (clean_link.find("-cgi") > -1 ):
              continue  # skip
            if clean_link.find(start_url)>-1: # ok
              # 6. If the link is new and valid, add it to the queue
              if clean_link not in visited_urls and clean_link not in queue:
                  queue.append(clean_link)

            else:
              clean_link = os.path.join(start_url,
                 os.path.split(clean_link)[-1])
              clean_link = remove_double_slash_except_at_start(clean_link)
              # 6. If the link is new and valid, add it to the queue
              if clean_link not in visited_urls and clean_link not in queue:
                  queue.append(clean_link)

    print(f"\nCrawl finished. Found {len(unique_urls)} unique pages.")
    return sorted(list(unique_urls))

def remove_double_slash_except_at_start(clean_link):
  clean_link = clean_link.replace("https://","ZZZ")
  clean_link = clean_link.replace("//","/")
  clean_link = clean_link.replace("ZZZ","https://")
  return clean_link
def save_urls_to_file(urls: list[str], filename: str):
    """Saves a list of URLs to a text file, one URL per line."""
    with open(filename, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(f"{url}\n")
    print(f"Successfully saved URLs to {filename}")

# --- Main Execution Block ---
if __name__ == "__main__":
    print("WARNING: SPECIFIC TO phenix documentation")
    START_URL = "https://phenix-online.org/version_docs/2.0-5723"
    OUTPUT_FILE = "discovered_urls.txt"
    args = sys.argv[1:]
    if len(args) > 0:
      START_URL = args[0]
    if len(args) > 1:
      OUTPUT_FILE = args[1]
    if (not START_URL.endswith("/")):
      START_URL+="/"

    if len(args) <= 2: # Phenix user docs
      extras = "reference tutorials overviews".split()
    else: #specify extra_paths with next arg
      extras = args[2].split()


    EXTRA_PATHS = [None]
    for extra in extras:
      EXTRA_PATHS.append("%s/%s/" %(START_URL,extra))
    print("START_URL: ",START_URL)
    print("EXTRA_PATHS", EXTRA_PATHS)
    print("OUTPUT_FILE", OUTPUT_FILE)

    crawled_urls = crawl_site(START_URL)

    if crawled_urls:
        save_urls_to_file(crawled_urls, OUTPUT_FILE)
