import urllib.request, urllib.parse, urllib.error
import ssl
import requests
import time
from bs4 import BeautifulSoup
from queue import PriorityQueue
from googlesearch import search
from urllib.parse import urljoin, urlparse
from url_normalize import url_normalize


# obtaining a seed set of pages from Google based on query
query = input("Please enter a search query ")
seed = search(query, stop=10)
urls = PriorityQueue()
urls_visited = {}
count = 0
RANK_IDX = 0
PAGES_CRAWLED_IDX = 1
NUM_HYPERLINKS_IDX = 2
NOVELTY_IDX = 3
IMPORTANCE_IDX = 4

log = open("log_file.txt", "w")
log.write("Beginning of the log file")

def print_urls():
    while not urls.empty():
        print(urls.get())


def update_score(urls_visited, domain_url, novelty_weight, importance_weight):
    if domain_url not in urls_visited:
        pages_crawled = 1
        curr_importance = 0
        num_hyperlinks = 1
    else:
        pages_crawled = urls_visited.get(domain_url)[PAGES_CRAWLED_IDX]
        curr_importance = urls_visited.get(domain_url)[IMPORTANCE_IDX]
        num_hyperlinks = urls_visited.get(domain_url)[NUM_HYPERLINKS_IDX]
    new_novelty = 1 / (pages_crawled + 1)
    priority = novelty_weight * new_novelty + importance_weight * curr_importance
    urls_visited[domain_url] = list((priority, pages_crawled + 1,
                                    num_hyperlinks, new_novelty, curr_importance))


def get_log(count, url, rank, curr_time):
    log_file = open("log_file.txt", "a")
    content = ["url # ", str(count), "\n", "url ", str(url), "\n",
                   "rank of visited url ", str(rank), "\n",
                   "visited at ", str(curr_time)]
    log_file.writelines(content)
    log_file.close()

# ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for webpage in seed:
    urls.put((- 1, webpage))

start_time = time.time()
seconds = 4
while not urls.empty():
    count += 1
    print("visited count is ", count)
    curr_time = time.time()
    # if curr_time - start_time > seconds:
    #     break
    curr_url = urls.get()
    curr_url = curr_url[1]
    try:
        response = requests.get(curr_url)
    except:
        pass
    if response.status_code == 200:
        curr_url_domain = urlparse(curr_url).netloc
        update_score(urls_visited, curr_url_domain, 0.5, 0.5)
        get_log(count, curr_url, urls_visited[curr_url_domain][RANK_IDX], curr_time)
        html_doc = response.text
        soup = BeautifulSoup(html_doc, 'html.parser')
        url_link_count = 0
        for url_link in soup.find_all('a', href=True):
            url_link_count += 1
            print("url link count is ", url_link_count)
            abs_url = urljoin(curr_url, url_link['href'])
            # normilize url
            curr_url = url_normalize(abs_url)
            domain_url = urlparse(curr_url).netloc
            update_score(urls_visited, domain_url, 0.5, 0.5)
            urls.put(tuple((- urls_visited[domain_url][RANK_IDX], curr_url)))


# print("The urls are", len(urls_visited))
# for url in urls_visited.items():
#     print(url)

# print_urls()
