# portal tjmg automation

## Installation
Use python3.6

sudo apt-get install wkhtmltopdf
pip install -r requirements.txt

## Run script via terminal
-number - list of search numbers

-csv_numbers - csv file with numbers

-csv_words - csv file with words

-download_folder - a place, where download pdf files if the folder doesn't exists will be created new if parameter not set, will save in a current folder

#### With csv file
```
python3 tjmg_automation.py -csv_numbers number.csv -csv_words words.csv -download_folder ./files/
```
1. Read numbers from the number.csv
2. Read numbers from the words.csv
3. Download pdf files in  ./files/ can be set absolute path as example(/home/ubuntu/intel_bot_sentenca_tjmg/)

#### With number list
```
python3 tjmg_automation.py -number 2008.001.184665-8 0156353-61.2014.8.19.0038 -csv_words words.csv -download_folder ./files/
```
1. Read numbers from the command line number split by space num1 num2 num3
2. Read numbers from the words.csv
3. Download pdf files in  ./files2/ will be created if doesn't exists

# How to use python module

#### With csv file
csv_parsing() - function save pdf files in work_folder.
```
from tjmg_automation import TjmgAutomation
search_words = ["Ver íntegra do(a) Sentença", "Tipo do Movimento"]
ja = TjmgAutomation(headless=True)
ja.csv_parsing(csv_file='number.csv',search_words, work_folder='./files/')
```
#### With number
search_process() - save pdf in work_folder and return text of pdf
```
from tjmg_automation import TjmgAutomation

search_words = ["Ver íntegra do(a) Sentença", "Tipo do Movimento"]
ja = TjmgAutomation(headless=True)
ja.search_process(number='2008.001.184665-8', search_word=search_words, work_folder='./')
ja.search_process(number='0156353-61.2014.8.19.0038', search_word=search_words, work_folder='./')
```
# How to kill process
press CTRL + C

if not help
```
ps -aux | grep 'tjmg_automation.py'
ubuntu   16875  1.3  0.7 104408 31584 pts/1    S+   20:36   0:11 python3 tjmg_automation.py -csv_file number.csv -download_folder ./files/
```
id process 16875
```
kill 16875
```
