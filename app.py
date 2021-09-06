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
urls.put((1, "https://en.wikipedia.org/wiki/Alan_Turing"))

for webpage in seed:
    print(webpage)

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