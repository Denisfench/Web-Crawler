import urllib.request, urllib.parse, urllib.error
import ssl
import requests
from bs4 import BeautifulSoup
from queue import PriorityQueue
from googlesearch import search

# obtaining a seed set of pages from Google based on query 
query = input("Please enter a search query ")
seed = search(query, stop=10)
urls = PriorityQueue()

for webpage in seed:
    urls.put((1, webpage))

# get the page ans scrape the data
data = []
# print("The first url is", urls.get()[1])
# might be getting stuck if the page doesn't respond 
for url in urls.queue:
    try:
        response = requests.get(url[1])
    except:
        pass
    if response.status_code == 200:
        print(response.headers)
        html_doc = response.text
        soup = BeautifulSoup(html_doc, 'html.parser')
        data.append(list((url, len(response.content), soup)))

# ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

html = urllib.request.urlopen("https://en.wikipedia.org/wiki/Alan_Turing", context=ctx).read()
soup = BeautifulSoup(html, 'html.parser')

tags = soup('a')
# for tag in tags:
#     # print(tag.get('href', None))

# for line in fhandle:
    # print(line.decode().strip())