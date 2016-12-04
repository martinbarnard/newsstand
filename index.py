#     _   __                       __                  __
#    / | / /__ _      ____________/ /_____ _____  ____/ /
#   /  |/ / _ \ | /| / / ___/ ___/ __/ __ `/ __ \/ __  / 
#  / /|  /  __/ |/ |/ (__  |__  ) /_/ /_/ / / / / /_/ /  
# /_/ |_/\___/|__/|__/____/____/\__/\__,_/_/ /_/\__,_/   
                                                       
# Description: Provides the latest news from a multitude of news sources.
# GitHub Repository: Newsstand (github.com/cryptopelago/newsstand)
# License: Unlicense (unlicense.org)

from config import *

# Load libraries
import requests
import urllib, os, json, yaml
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash 
import dateutil.parser
import datetime

import os
# 21co wallet 
print('importing two1 stuff')
from two1.wallet import Wallet
from two1.bitserv.flask import Payment
# 
# 
from random import choice

#
# Using mongodb
from pymongo import MongoClient 
print("pymongo started")
#
# for generating unique ids
from hashlib import sha256
ids=lambda st : sha256(st.encode('utf-8'))


import threading, time
sleepytime= lambda  mins:  mins * 60
threads=[]

def init_db():
    client = MongoClient()
    cl = client.newsstand
    print('yeah baby')
    return cl.articles

db = init_db()

app = Flask(__name__)

# 21.co wallet & payment
# Init Flask, Wallet and Payment
print("Initiating wallet stuff")
wallet = Wallet()
payment = Payment(app, wallet)
print("Wallet initiated")

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

@app.route('/')
def index():
    nw=datetime.datetime.now()
    hrs=datetime.timedelta(hours=1)
    after=nw - hrs
    print("Getting rows...")
    rows=db.find({'date':{'$gt':after}})
    print("Rows gotten")
    return render_template('index.html', rows=rows)

@app.route('/news')
#@payment.required(900)
def get_articles():
    '''
    pulls from our database which is set to 
    update every n-minutes
    args are:
    source 
    categories 
    before - time: %Y-%m-%d %H:%M:%S
    after - time: %Y-%m-%d %H:%M:%S
    '''
    # TODO:  Utilise these
    source      = request.args.get('source','all')
    categories  = request.args.get('categories', 'all')
    before      = request.args.get('before', '')
    after       = request.args.get('after', '')
    author      = request.args.get('author', '')

    # fields here...
    nw=datetime.datetime.now()
    hrs=datetime.timedelta(hours=1)
    after=nw - hrs
    rv=['{}'.format(source)]
    rows=db.find({'date':{'$gt':after}})
#    rows=db.find()
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
    return json.dumps(rv[1:])




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
    #xx=add_records(db,bl)
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



# Init Host
if __name__=='__main__':
    # TODO: Remove the  threaded daemon and put it in it's own file
    # TODO: Wrap this in a loop &/or generate a config
    # file if none exists
    sourceList=get_sources()
    for s in sourceList:
        t = threading.Thread(target=articles, args=(s, ))
        t.start()
        threads.append(t)

    print("initalising...")
    app.run(host='::', port=port)
