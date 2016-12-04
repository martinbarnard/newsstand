import requests
import dateutil.parser
import datetime
from pymongo import MongoClient 
import threading, time
import urllib, os, json, yaml
from config import *
threads=[]
#
# for generating unique ids
from hashlib import sha256
ids=lambda st : sha256(st.encode('utf-8'))
sleepytime= lambda  mins:  mins * 60

# init our db
def init_db():
    client = MongoClient()
    cl = client.newsstand
    print("daemon running. db init")
    return cl.articles
# Start our daemon
db = init_db()

def get_sources():
    '''
    Pull sources from our api
    '''
    sl=[]
    url=requests.get(newsapi + 'sources')
    p=json.loads(url.text)
    for s in p['sources']:
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
    #xx=add_records(db,bl)
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
        print("awake & getting {}".format(src['id']))
        srcstring = 'source={}'.format(src['id'])
        for cat in categories:
            urlcat="&category={}".format(cat)
            urlstring=newsapi + 'articles?' + srcstring + urlcat + '&apiKey=' + key
            rvs=get_url(urlstring)
            add_records(db, rvs, cat, src['id'])
        time.sleep(tts)


def add_records(coll,recs, cat, src):
    '''
    add records to coll 
    '''
    tora=datetime.datetime.now()
    rvs=[]
    # recs is a list
    if  recs:
        for r in recs:
            x=ids(r['url'])
            xd =x.hexdigest()
            r['_id']=xd
            r['src']=src
            r['category']=cat
            datestring=r['publishedAt']
            if datestring:
                try:
                    yourdate = dateutil.parser.parse(datestring)
                    r['date']=yourdate
                except AttributeError:
                    r['date']=tora
                    print("can't format date {}".format(datestring))
                except OverflowError:
                    print("fuck overflows")
            else:
                r['date']=tora
            if not coll.find_one({'_id':xd}):
                try:
                    coll.insert_one(r)
                    print(">>> {} {}".format(src,r['title']))
                except OverflowError:
                    # we get here with the times of india having fucked up dates
                    print("we're in overflowzzz {}".format(r))
                    r['date']=datetime.datetime.now()
                    try:
                        coll.insert_one(r)
                    except:
                        print("Fuck it's all died")
    else:
        print("No articles in {}".format(recs))
    return 0


sourceList=get_sources()
for s in sourceList:
    t = threading.Thread(target=articles, args=(s, ))
    t.start()
    threads.append(t)
