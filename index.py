#     _   __                       __                  __
#    / | / /__ _      ____________/ /_____ _____  ____/ /
#   /  |/ / _ \ | /| / / ___/ ___/ __/ __ `/ __ \/ __  / 
#  / /|  /  __/ |/ |/ (__  |__  ) /_/ /_/ / / / / /_/ /  
# /_/ |_/\___/|__/|__/____/____/\__/\__,_/_/ /_/\__,_/   
                                                       
# Description: Provides the latest news from a multitude of news sources.
# GitHub Repository: Newsstand (github.com/cryptopelago/newsstand)
# License: Unlicense (unlicense.org)

# Load libraries
import requests
import urllib, os, json, yaml
from flask import Flask, request, jsonify
import dateutil.parser
import datetime

# 21co wallet 
print('importing two1 stuff')
from two1.wallet import Wallet
from two1.bitserv.flask import Payment
from random import choice
import argparse
# Using mongodb
from pymongo import MongoClient 
# for generating unique ids
from hashlib import sha256
ids=lambda st : sha256(st.encode('utf-8'))


import threading, time
# TODO: threading to periodically pull all sources...
# TODO: use 10' timer to pull all sources and then provide an aggregate here...
tsecs=60*60
threads=[]

def init_db():
    client = MongoClient()
    db = client.newsstand
    return db.articles

db = init_db()

key='f26c6e07aac5401eb95f71a9c4f70db1'
app = Flask(__name__)
parser = argparse.ArgumentParser()
parser.add_argument('-p','--port', help="which port to start on", type=int, default=10254)
args=parser.parse_args()
# Init Flask, Wallet and Payment
wallet = Wallet()
payment = Payment(app, wallet)
# TODO: Store all articles received in db
# Don't like these hard-coded. Maybe store in config later?
categories = [ 
        'business', 'entertainment', 
        'gaming', 'general', 'music', 
        'science-and-nature', 'sport', 'technology' 
        ]
languages = ['en', 'de', 'fr']
countries = [
        'au', 'de', 'gb', 'in', 'it', 'us'
        ]

newsapi='https://newsapi.org/v1/'
# our list of sources
sourceList=[]


################################################################################
# Routed functions
################################################################################
@app.route('/sources')
def sources():
    '''
    Display a list of sources
    '''
    rval=[]
    for s in sourceList:
        rval.append(s['id'])
    return json.dumps(rval)

@app.route('/news')
#@payment.required(900)
def get_articles():
    '''
    pulls from our database which is set to 
    update every n-minutes
    '''
    source=request.args.get('source','all')
    categories=request.args.get('articles', 'all')

    # fields here...
    tora=datetime.datetime.now()
    hrs=datetime.timedelta(hours=6)
    after=tora - hrs
    rv=[]
    rows=db.find({'date':{'$gt':after}})
    if rows:
        for row in rows:
            k={}
            # todo omit key of date
            for r in row.keys():
                if r!='date':
                    k[r]=row[r]
                else:
                    k[r]=row[r].strftime('%Y-%m-%d %H:%M:%S')
            rv.append(k)
    return json.dumps(rv)




################################################################################
# private functions
################################################################################
def get_url(urlstring, ttls=None):
    '''
    function to get the data from the url
    expects urlstring to be complete.
    '''
    url = requests.get(urlstring)
    titles=[]
    bl=json.loads(url.text)
    xx=add_records(db,bl)
    return bl['articles']

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

def articles(src,categories=categories,key=key, db=db, tsecs=tsecs):
    '''
    update db with latest articles from src with cat
    will be threaded
    expects:
    src - string of source id
    returns - nothing
    '''
    while True:
        srcstring = 'source={}'.format(src['id'])
        for cat in categories:
            urlcat="&category={}".format(cat)
            urlstring=newsapi + 'articles?' + srcstring + urlcat + '&apiKey=' + key 
            rvs=get_url(urlstring)
            add_records(db, rvs)
        time.sleep(tsecs)


def add_records(coll,recs):
    '''
    add records to coll 
    '''
    tora=datetime.datetime.now()
    rvs=[]
    # recs is a list
    if 'articles'  in recs:
        for r in recs['articles']:
            x=ids(r['url'])
            xd =x.hexdigest()
            r['_id']=xd
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
                    print(">>> INSERTING {}".format(r['title']))
                    coll.insert_one(r)
                except OverflowError:
                    # we get here with the times of india having fucked up dates
                    print("we're in overflowzzz {}".format(r))
                    r['date']=datetime.datetime.now()
                    try:
                        coll.insert_one(r)
                    except:
                        print("Fuck it's all died")
    return 0


# Init Host
if __name__=='__main__':
    port=args.port
    sourceList=get_sources()
    for s in sourceList:
        t = threading.Thread(target=articles, args=(s,))
        t.start()
        threads.append(t)

    print("initalising...")
    app.run(host='::', port=port)
