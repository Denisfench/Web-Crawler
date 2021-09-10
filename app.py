import urllib.request, urllib.parse, urllib.error
import ssl
import requests
from bs4 import BeautifulSoup
from queue import PriorityQueue
from googlesearch import search
from urllib.parse import urljoin
from url_normalize import url_normalize

# obtaining a seed set of pages from Google based on query 
query = input("Please enter a search query ")
seed = search(query, stop=10)
urls = PriorityQueue()
urls_visited = {}
data = []

# ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for webpage in seed:
    urls.put((1, webpage))

# get the page ans scrape the data
for url in urls.queue:
    try:
        response = requests.get(url[1])
    except:
        pass
    if response.status_code == 200:
        html_doc = response.text
        soup = BeautifulSoup(html_doc, 'html.parser')
        data.append(list((url[1], len(response.content), url[0], soup)))

# scrape the pages for the links to other pages
for page in data:
    base_url = page[0]
    for url_link in page[3].find_all('a', href=True):
        abs_url = urljoin(base_url, url_link['href'])
        urls.put(tuple((1, abs_url)))
        # normilize url
        curr_url = url_normalize(abs_url)
        if curr_url not in urls_visited:
            urls_visited[curr_url] = 1
        else:
            num_visited = urls_visited[curr_url]
            urls_visited[curr_url] = num_visited + 1


print("The urls are", len(urls_visited))
for url in urls_visited.items():
    print(url)


def print_urls():
    while not urls.empty():
        print(urls.get())
