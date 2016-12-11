import requests
import dateutil.parser
import datetime
from pymongo import MongoClient 
import threading, time
import urllib, os, json, yaml
import logging, sys
logging.basicConfig(strem=sys.stderr, level=logging.DEBUG)

from config import *
threads=[]
DEBUG=True
#
# for generating unique ids
from hashlib import sha1
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
    logging.info('pulling source list')
    return cl.sources

# Start our daemon
db = init_db()
srcs=init_srcs()

def get_sources(srcs=srcs):
    '''
    Pull sources from our api
    '''
    sl=[]
    url=requests.get(newsapi + 'sources')
    p=json.loads(url.text)
    for s in p['sources']:
        logging.debug("adding {} to sources".format(s['id']))
        res=srcs.find({'_id':s['id']})
        if res.count() <= 1:
            try:
                s['_id']=s['id']
                srcs.insert_one(s)
            except:
                logging.debug('failed to insert duplicate key')
                pass

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
        logging.debug("awake & getting {}".format(src['id']))
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
            datestring=r['publishedAt']
            if datestring:
                try:
                    yourdate = dateutil.parser.parse(datestring)
                    r['date']=yourdate
                except AttributeError:
                    logging.debug("ATTRIBUTEERROR!!!")
                    r['date']=currently
                except OverflowError:
                    logging.debug("OVERFLOWEERROR!!!")
                    pass
            else:
                r['date']=currently

            res = db.find({'_id':x}).limit(1)
            if res.count() < 1:
                try:
                    db.insert_one(r)
                except Exception as e: 
                    logging.debug("unable to insert record: {}".format(r['_id']))
                    logging.debug("Error message:  {}".format(e))

                    pass

            else:
                pass
    else:
        logging.info("No articles in {}".format(rvs))
    return 0


sourceList=get_sources()

for s in sourceList:
    t = threading.Thread(target=articles, args=(s, ))
    t.start()
    threads.append(t)
