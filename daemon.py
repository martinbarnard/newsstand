import requests
import dateutil.parser
import datetime
from pymongo import MongoClient 
import threading, time
import urllib, os, json, yaml
import logging, sys
from config import *
from hashlib import sha1
# NLTK >> Maybe we should use separate module for this?
import nltk
from nltk.corpus import stopwords
stopset = set(stopwords.words('english'))
threads=[]
# TODO: loglevel, etc.
def ids(inst):
    '''
    Generate unique hash for url. Should be fairly fast and unique with sha1
    '''
    return sha1(inst.encode('utf-8')).hexdigest()

sleepytime= lambda  mins:  mins * 60

# init our db
def init_db():
    client = MongoClient()
    cl = client.newsstand
    logging.info("daemon running. db init")
    return cl.articles

def init_srcs():
    client=MongoClient()
    cl=client.newsstand
#    logging.debug('pulling source list')
    return cl.sources


#
# Start our daemon
#
db = init_db()
srcs=init_srcs()
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_PRIVATE = os.path.join(APP_ROOT,'private')
def load_sentiment(sentimentData = 'AF.txt'):
    ''' (file) -> dictionary
    This method should take your sentiment file
    and create a dictionary in the form {word: value}
    '''
    afinnfile = open(os.path.join(APP_PRIVATE, sentimentData),'r')
    scores = {} # initialize an empty dictionary
    for line in afinnfile:
        term, score  = line.split("\t")  # The file is tab-delimited. "\t" means "tab character"
        scores[term] = float(score)  # Convert the score to an integer.
    return scores # Print every (term, score) pair in the dictionary

def get_sources(srcs=srcs, lang='en'):
    '''
    Pull sources from our api
    '''
    sl=[]
    url=requests.get(newsapi + 'sources')
    p=json.loads(url.text)
    for s in p['sources']:
        res=srcs.find({'_id':s['id']})
        if res.count() <= 1:
            try:
                s['_id']=s['id']
                srcs.insert_one(s)
            except:
#                logging.debug('failed to insert duplicate key - updating {}'.format(s['id']))
                srcs.save(s)
                pass

        if s['language']==lang:
            sl.append(s)
    return sl

def get_url(urlstring, ttls=None):
    '''
    function to get the data from the url
    expects urlstring to be complete.
    '''
    url = requests.get(urlstring)
    titles=[]
    bl=json.loads(url.text)
    return bl['articles']


def articles(src, db=db):
    '''
    update db with latest articles from src with cat
    will be threaded
    expects:
    src - string of source id
    returns - nothing
    '''
    tts=sleepytime(sleep_minutes)
    while True:
#        logging.debug("awake & getting {}".format(src['id']))
        srcstring = 'source={}'.format(src['id'])
        for cat in categories:
            urlcat="&category={}".format(cat)
            urlstring=newsapi + 'articles?' + srcstring + urlcat + '&apiKey=' + key
            rvs=get_url(urlstring)
            add_records(db, rvs,  src)
        time.sleep(tts)

def add_records(db,rvs, src):
    '''
    add records to db 
    '''
    currently=datetime.datetime.now()
    src_id=src['id']
    if  rvs:
        for r in rvs:
            x=ids(r['url'])
            r['_id']=x
            r['src']=src_id
            r['category']=src['category']
            # TODO: Build a better stopwords list
            # maybe greater than n-chars
            if r['description'] != None and len(r['description']) > 20:
                r['tokens']  = nltk.word_tokenize(r['description'])
                r['tokens'] = [word.lower() for word in r['tokens'] if word not in stopset and len(word) > 4]
            else:
                r['tokens'] = []
            datestring=r['publishedAt']
            if datestring:
                try:
                    yourdate = dateutil.parser.parse(datestring)
                    r['date']=yourdate
                except AttributeError:
                    r['date']=currently
                except OverflowError:
                    pass
            else:
                r['date']=currently

            res = db.find({'_id':x}).limit(1)
            if res.count() < 1:
                try:
                    db.insert_one(r)
                except Exception as e: 
                    # Usually timestamp error
                    r['date'] = currently
                    db.insert_one(r)

                    pass

            else:
                pass
    else:
#        logging.info("No articles in {}".format(rvs))
        pass
    return 0

sourceList=get_sources()
#
# Global scores dict
#
scores=load_sentiment()
for s in sourceList:
    t = threading.Thread(target=articles, args=(s, ))
    t.start()
    threads.append(t)
