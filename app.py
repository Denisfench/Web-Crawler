import urllib.request, urllib.parse, urllib.error
import ssl
import requests
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from queue import PriorityQueue
from googlesearch import search
from urllib.parse import urljoin, urlparse
from urllib import robotparser
from url_normalize import url_normalize
from threading import Thread

# obtaining a seed set of pages from Google based on query
query = input("Please enter a search query ")
NUM_SEED_PAGES = 10
seed = search(query, stop=10) # MAJOR BUG HERE, we aren't able to loop over the seed pages
# seed = ['https://en.wikipedia.org']
urls = PriorityQueue()
urls_visited = {}
count = 0
RANK_IDX = 0
PAGES_CRAWLED_IDX = 1
NOVELTY_IDX = 2
IMPORTANCE_IDX = 3
DEBUG = False
CRAWLER_NAME = "NYU_Crawler"
THREAD_POOL_SIZE = 20

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}

# format_blacklist = {".aac", ".avi", ".bin", ".csh", ".css", ".gif", ".ico", ".ics", ".jar", 
#                     ".jpeg", ".jpg", ".js", ".mp3", ".mpeg", ".mpkg", ".oga", ".ogv", ".opus", 
#                     ".png", ".ppt", ".sh", ".tar", ".xls"}

mime_type_blacklist = {"audio/aac", "video/x-msvideo", "application/octet-stream", "application/x-csh", 
                        "text/css", "text/csv", "application/msword", "image/gif", "text/calendar", 
                        "image/jpeg", "text/javascript", "audio/mpeg", "video/mp4", "video/mpeg", 
                        "image/png", "application/vnd.ms-powerpoint", "application/zip"}

success_respose = {200, 201, 202, 203, 204, 205, 206, 207, 208, 226}
# print("seed start")
# print()
# for webpage in seed:
#     print(webpage)
# print("seed end")

log = open("log_file.txt", "w")
log.write("Beginning of the log file")
df = pd.DataFrame(columns=["url", "response code", "novelty score", "importance score", "url_rank", "visited_at", "webpage_size"])

def print_urls():
    while not urls.empty():
        print(urls.get())

# importance corresponds to the number of hyperlinks we've encountered to the given
# website, we need to remove the number of hyperlinks paramater from the urls_visited
# dictionary
def update_score(urls_visited, domain_url, novelty_weight, importance_weight, crawling=False, see_again=True):
        if domain_url not in urls_visited and crawling:
            pages_crawled = 1
            curr_importance = 1
            new_novelty = 1 / (pages_crawled + 1)
            priority = novelty_weight * new_novelty + importance_weight * curr_importance
            urls_visited[domain_url] = list((priority, pages_crawled, new_novelty, curr_importance))
        elif domain_url not in urls_visited and see_again:
            pages_crawled = 0
            curr_importance = 0
            curr_novelty = 1
            priority = novelty_weight * curr_novelty + importance_weight * curr_importance
            urls_visited[domain_url] = list((priority, pages_crawled, curr_novelty, curr_importance))
        elif crawling:
            pages_crawled = urls_visited.get(domain_url)[PAGES_CRAWLED_IDX] + 1
            curr_importance = urls_visited.get(domain_url)[IMPORTANCE_IDX]
            new_novelty = 1 / (pages_crawled + 1)
            priority = novelty_weight * new_novelty + importance_weight * curr_importance
            urls_visited[domain_url] = list((priority, pages_crawled, new_novelty, curr_importance))
        elif see_again:
            pages_crawled = urls_visited.get(domain_url)[PAGES_CRAWLED_IDX]
            new_importance = urls_visited.get(domain_url)[IMPORTANCE_IDX] + 1
            curr_novelty = urls_visited.get(domain_url)[NOVELTY_IDX]
            priority = novelty_weight * curr_novelty + importance_weight * new_importance
            urls_visited[domain_url] = list((priority, pages_crawled, curr_novelty, new_importance))


# can be parallelized
def crawler_allowed(root_url, crawled_url):
    rp = robotparser.RobotFileParser()
    url_scheme = urlparse(crawled_url).scheme + "://"
    root_url = url_scheme + root_url
    robots_url = '{}/robots.txt'.format(root_url)
    rp.set_url(robots_url)
    try:
        rp.read()
    except:
        pass
    if rp.can_fetch(CRAWLER_NAME, crawled_url):
        return True
    return False

# time format is bad
def get_log(count, url, novelty, importance, rank, curr_time, content_length, response_code, txt=False):
    dt = datetime.now().strftime("%H:%M:%S")

    if txt:
        log_file = open("log_file.txt", "a")
        content = ["url # ", str(count), "\n", "url ", str(url), "\n",
                   "rank of visited url ", str(rank), "\n",
                   "visited at ", str(curr_time)]
        log_file.writelines(content)
        log_file.close()
    else:
        data = {"url": url, "response code": response_code, "novelty score": novelty, "importance score": importance, "url_rank": rank, "visited_at": dt, "webpage_size": content_length}
        df.loc[len(df.index)] = data
        df.to_csv('log_file.csv', index=False)


# ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


# print("seed start")
# for webpage in seed:
#     print(webpage)
# print("seed end")

# need to add robot exclusion check to seed urls 
for webpage in seed:
    if DEBUG:
        print(webpage)
    urls.put((- 1, webpage))
    webpage_domain = urlparse(webpage).netloc
    update_score(urls_visited, webpage_domain, 0.5, 0.5)

start_time = time.time()
seconds = 10
# has to be parallelized
def crawl_pages():
    count = 0
    while not urls.empty():
        count += 1
        curr_time = time.time()
        print("visited count is ", count)
        if DEBUG:
            print("visited count is ", count)
            if curr_time - start_time > seconds:
                break
        curr_url = urls.get()
        curr_rank = curr_url[0]
        curr_url = curr_url[1]
        print("curr url is ", curr_url)
        curr_url_domain = urlparse(curr_url).netloc
        if not crawler_allowed(curr_url_domain, curr_url): continue
        updated_rank = urls_visited[curr_url_domain][RANK_IDX]
        if DEBUG:
            print("updated rank is ", updated_rank)
            print("curr rank is", curr_rank)
        if updated_rank != - curr_rank:
            urls.put(tuple((- updated_rank, curr_url)))
            continue
        try:
            response = requests.get(curr_url, timeout=10, headers=headers)
        except:
            pass
        if response.status_code in success_respose:
            # check the mime type of the content
            # we are making a duplicate network request here 
            # we might want to eliminate requsts module and use urlib only instead 
            try:
                with urllib.request.urlopen(curr_url) as response_content:
                    mime_type = response_content.info().get_content_type()
                if mime_type in mime_type_blacklist: continue
            except: continue
            try:
                # content_length = response.headers['content-length'] not neccessarily present
                content_length = len(response.content)
                update_score(urls_visited, curr_url_domain, 0.5, 0.5, crawling=True, see_again=False)
                get_log(count, curr_url, urls_visited[curr_url_domain][NOVELTY_IDX], urls_visited[curr_url_domain][IMPORTANCE_IDX],urls_visited[curr_url_domain][RANK_IDX], 
                        curr_time, content_length, response.status_code)
                html_doc = response.text
                soup = BeautifulSoup(html_doc, 'html.parser')
                url_link_count = 0
                for url_link in soup.find_all('a', href=True):
                    url_link_count += 1
                    if DEBUG:
                        print("url link count is ", url_link_count)
                    abs_url = urljoin(curr_url, url_link['href'])
                    # normilize url
                    curr_url = url_normalize(abs_url)
                    domain_url = urlparse(curr_url).netloc
                    if domain_url in urls_visited:
                        update_score(urls_visited, domain_url, 0.5, 0.5)
                    else:
                        update_score(urls_visited, domain_url, 0.5, 0.5)
                        urls.put(tuple((- urls_visited[domain_url][RANK_IDX], curr_url)))
            except:
                print("Unable to parse ", curr_url)
        else:
            get_log(- 1, curr_url, urls_visited[curr_url_domain][NOVELTY_IDX], urls_visited[curr_url_domain][IMPORTANCE_IDX], urls_visited[curr_url_domain][RANK_IDX], curr_time, - 1, response.status_code, txt=False)


def main():
    threads = [
        Thread(target=crawl_pages)
        for _ in range(THREAD_POOL_SIZE)
    ]
    for thread in threads:
        thread.start()
    while threads:
        threads.pop().join()
    # crawl_pages()

if __name__ == "__main__":
    started = time.time()
    main()
    elapsed = time.time() - started
    print()
    print("time elapsed: {:.2f}s".format(elapsed))