import urllib.request, urllib.parse, urllib.error
import ssl
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from queue import PriorityQueue
from googlesearch import search
from urllib.parse import urljoin, urlparse
from urllib import robotparser
from urllib.robotparser import RobotFileParser
from url_normalize import url_normalize
from threading import Thread

# obtaining a seed set of pages from Google based on query
query = input("Please enter a search query ")
NUM_SEED_PAGES = 10
seed = search(query, stop=NUM_SEED_PAGES) 
urls = PriorityQueue()
urls_visited = {}
count = 0
RANK_IDX = 0
PAGES_CRAWLED_IDX = 1
NOVELTY_IDX = 2
IMPORTANCE_IDX = 3
DEBUG = False
CRAWLER_NAME = "NYU_Crawler"
THREAD_POOL_SIZE = 60

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}

# defining a blacklist of mime types
mime_type_blacklist = {"audio/aac", "video/x-msvideo", "application/octet-stream", "application/x-csh", 
                        "text/css", "text/csv", "application/msword", "image/gif", "text/calendar", 
                        "image/jpeg", "text/javascript", "audio/mpeg", "video/mp4", "video/mpeg", 
                        "image/png", "application/vnd.ms-powerpoint", "application/zip"}

# defining a hashset of success responses
success_respose = {200, 201, 202, 203, 204, 205, 206, 207, 208, 226}

# creating a dataframe for the log file
df = pd.DataFrame(columns=["url", "response code", "novelty score", "importance score", "url_rank", "visited_at", "webpage_size"])

# modifying the Robot File Parser class in order to give the Robot Parser object a lower timeout
class TimoutRobotFileParser(RobotFileParser):
    def __init__(self, url='', timeout=5):
        super().__init__(url)
        self.timeout = timeout

    def read(self):
        """Reads the robots.txt URL and feeds it to the parser."""
        try:
            f = urllib.request.urlopen(self.url, timeout=self.timeout)
        except urllib.error.HTTPError as err:
            if err.code in (401, 403):
                self.disallow_all = True
            elif err.code >= 400:
                self.allow_all = True
        else:
            raw = f.read()
            self.parse(raw.decode("utf-8").splitlines())

# adding a function that prints a Priority Queue of urls for debugging purposes
def print_urls():
    while not urls.empty():
        print(urls.get())

# update_score fucntion ensures that the urls in the urls_visited dictionary always have up to date scores
def update_score(urls_visited, domain_url, novelty_weight, importance_weight, crawling=False, see_again=True):
        # the url wasn't encountered before and we are currently crawling the url
        if domain_url not in urls_visited and crawling:
            pages_crawled = 1
            curr_importance = 1
            new_novelty = 1 / (pages_crawled + 1)
            priority = novelty_weight * new_novelty + importance_weight * curr_importance
            urls_visited[domain_url] = list((priority, pages_crawled, new_novelty, curr_importance))
        # the url wasn't encountered before and we are currently parsing the url
        elif domain_url not in urls_visited and see_again:
            pages_crawled = 0
            curr_importance = 0
            curr_novelty = 1
            priority = novelty_weight * curr_novelty + importance_weight * curr_importance
            urls_visited[domain_url] = list((priority, pages_crawled, curr_novelty, curr_importance))
        # the url was encountered before and we are currently crawling the url
        elif crawling:
            pages_crawled = urls_visited.get(domain_url)[PAGES_CRAWLED_IDX] + 1
            curr_importance = urls_visited.get(domain_url)[IMPORTANCE_IDX]
            new_novelty = 1 / (pages_crawled + 1)
            priority = novelty_weight * new_novelty + importance_weight * curr_importance
            urls_visited[domain_url] = list((priority, pages_crawled, new_novelty, curr_importance))
        # the url was encountered before and we are currently parsing the url
        elif see_again:
            pages_crawled = urls_visited.get(domain_url)[PAGES_CRAWLED_IDX]
            new_importance = urls_visited.get(domain_url)[IMPORTANCE_IDX] + 1
            curr_novelty = urls_visited.get(domain_url)[NOVELTY_IDX]
            priority = novelty_weight * curr_novelty + importance_weight * new_importance
            urls_visited[domain_url] = list((priority, pages_crawled, curr_novelty, new_importance))


# crawler_allowed function implements robot exclusion protocol
def crawler_allowed(root_url, crawled_url):
    # rp = robotparser.RobotFileParser()
    rp = TimoutRobotFileParser()
    url_scheme = urlparse(crawled_url).scheme + "://"
    root_url = url_scheme + root_url
    robots_url = '{}/robots.txt'.format(root_url)
    rp.set_url(robots_url)
    try:
        rp.read()
    except:
        return False
    if rp.can_fetch(CRAWLER_NAME, crawled_url):
        return True
    return False

# get_log function generates a log file by appending rows with the new crawled urls to the log csv file
def get_log(url, novelty, importance, rank, content_length, response_code):
    # appending the data to the Pandas DataFrame
    dt = datetime.now().strftime("%H:%M:%S")
    data = {"url": url, "response code": response_code, "novelty score": novelty, "importance score": importance, "url_rank": rank, "visited_at": dt, "webpage_size": content_length}
    df.loc[len(df.index)] = data
    # converting the DataFrame to the csv format
    df.to_csv('log_file.csv', index=False)


# ignoring SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


# setting the initial scores of the pages from the seed set of pages
for webpage in seed:
    if DEBUG:
        print(webpage)
    webpage_domain = urlparse(webpage).netloc
    if crawler_allowed(webpage_domain, webpage):
        urls.put((- 1, webpage))
        update_score(urls_visited, webpage_domain, 0.5, 0.5)


if DEBUG:
    count = 0
    start_time = time.time()
    seconds = 10

# core function that crawles and parses the webpages
def crawl_pages():
    while not urls.empty():
        if DEBUG:
            curr_time = time.time()
            if curr_time - start_time > seconds:
                break
        # retrieving a url from the Priority Queue
        curr_url = urls.get()
        curr_rank = curr_url[0]
        curr_url = curr_url[1]
        print("currently crawling ", curr_url)
        curr_url_domain = urlparse(curr_url).netloc
        # checking whether our crawler is allowed on the webpage
        if not crawler_allowed(curr_url_domain, curr_url): continue
        # updating the rank of the webpage based on our attempt to crawl it
        updated_rank = urls_visited[curr_url_domain][RANK_IDX]
        if DEBUG:
            print("updated rank is ", updated_rank)
            print("curr rank is", curr_rank)
        # if the rank of the webpage in the priority queue has changed since our last retrival,
        # update the rank and put it back into the queue. If during the next iteration the
        # page will still have the highest rank, we will crawl it
        if updated_rank != - curr_rank:
            urls.put(tuple((- updated_rank, curr_url)))
            continue
        # attempting to get the webpage from the server
        try:
            response = urllib.request.urlopen(curr_url, timeout=5) # guesstype check
        except: 
            print("Unable to get a response from ", curr_url)
            continue
        # checking the response code of the server if one was received
        if response.getcode() in success_respose:
            # checking the content mime type, if its not on the blacklist, we continue
            mime_type = response.info().get_content_type()
            if mime_type in mime_type_blacklist: continue
            # parsing the content of the webpage
            try:
                content = response.read()
                # calculating the length of the content
                content_length = len(content)
                # updating the score of the url in the dictionary based on us seeing the url while parsing
                update_score(urls_visited, curr_url_domain, 0.5, 0.5, crawling=True, see_again=False)
                # appending the data collected from the url to the log file
                get_log(curr_url, urls_visited[curr_url_domain][NOVELTY_IDX], urls_visited[curr_url_domain][IMPORTANCE_IDX],urls_visited[curr_url_domain][RANK_IDX], 
                        content_length, response.getcode())
                html_doc = content.decode('utf-8')
                soup = BeautifulSoup(html_doc, 'html.parser')
                # looking for links to other urls on the webpage
                for url_link in soup.find_all('a', href=True):
                    if DEBUG:
                        url_link_count = 0
                        url_link_count += 1
                        print("url link count is ", url_link_count)
                    abs_url = urljoin(curr_url, url_link['href'])
                    # normilizing url
                    curr_url = url_normalize(abs_url)
                    domain_url = urlparse(curr_url).netloc
                    # storing the links or updating their rank in the urls found dictionary
                    if domain_url in urls_visited:
                        update_score(urls_visited, domain_url, 0.5, 0.5)
                    else:
                        update_score(urls_visited, domain_url, 0.5, 0.5)
                        # adding the newly found urls to the Priority Queue if they weren't added there before
                        urls.put(tuple((- urls_visited[domain_url][RANK_IDX], curr_url)))
            except:
                print("Unable to parse ", curr_url)
        else:
            # generating a log file for the urls with non-successful status code
            get_log(curr_url, urls_visited[curr_url_domain][NOVELTY_IDX], urls_visited[curr_url_domain][IMPORTANCE_IDX], urls_visited[curr_url_domain][RANK_IDX], - 1, response.getcode(), txt=False)


def main():
    # creating a pool of threads that will be working on the crawl_pages() function
    threads = [
        Thread(target=crawl_pages)
        for _ in range(THREAD_POOL_SIZE)
    ]

    # starting the threads 
    for thread in threads:
        thread.start()

    # joining the threads 
    while threads:
        threads.pop().join()

if __name__ == "__main__":
    started = time.time()
    main()
    elapsed = time.time() - started
    print()
    print("time elapsed: {:.2f}s".format(elapsed))