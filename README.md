**To run the web crawler, please follow the instructions below:**

1. Install project dependencies from the requirements.txt file by running ```pip3 install -r requirements.txt``` (Please note that ```time``` and ```urllib``` modules shouldn't have been included in the requirements file and should be excluded prior to running the file). 
2. To run the crawler, we can use ```python3 app.py```
3. Enter a search query 
4. URLs that are currently being crawled will be displayed on the screen. Also, a ```log_file.csv``` will be generated containing the names of the URLs that we've crawled, response codes, novelty scores, importance scores, URL ranks, the time URLs were visited, and the webpage sizes. 

The project on Brightspace contains the following files:

- ```app.py```: the crawler application file
- ```requirements.txt```: the file containing Python dependencies used by the project
- ```demo_log_file.csv```: the log file from the demo on Monday (09.20.2021)
- ```log_files```: a directory containing a log file for the ```Paris texas``` query generated on 09.19.2021 and terminated prematurely (before crawling > 10 000 pages)

*Please discard other files in the folder. Sorry for attaching them!*

*Note: since my submission on Brightspace on Monday I've created a README.md and a crawler_design.md files. I've removed unnecessary dependencies from the ```requirements.txt``` file. Also, I've added some commends to the app.py file and removed some of the redundant comments from the same file. In addition, I've added a timeout value for the requests sent by the robotparser library. Finally, I've generated extra log files as was specified by the submission requirements for the ```paris texas``` and ```brooklyn union``` queries. 

