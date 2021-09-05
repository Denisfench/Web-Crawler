import urllib.request, urllib.parse, urllib.error
import ssl
from bs4 import BeautifulSoup

# ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

html = urllib.request.urlopen("https://en.wikipedia.org/wiki/Alan_Turing").read()
soup = BeautifulSoup(html, 'html.parser')

tags = soup('a')
for tag in tags:
    print(tag.get('href', None))

# for line in fhandle:
#     print(line.decode().strip())