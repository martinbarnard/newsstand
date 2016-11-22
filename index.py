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
from flask import Flask, request
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


# TODO: threading to periodically pull all sources...
# TODO: use 10' timer to pull all sources and then provide an aggregate here...
#tsecs=10*60


def init_db():
    client = MongoClient()
    db = client.newsstand
    return db.articles

db = init_db()
print("db initialised")

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

def get_sources():
    sl=[]
    url=requests.get(newsapi + 'sources')
    p=json.loads(url.text)
    for s in p['sources']:
        sl.append(s)
    return sl

@app.route('/sources')
def sources():
    rval=[]
    for s in sourceList:
        rval.append(s['id'])
    print('yeah')
    return json.dumps(rval)

@app.route('/news')
#@payment.required(900)
def get_articles():
    source=request.args.get('source') 
    ttls=request.args.get('titles')
    if source == None:
        source=choice(sourceList)
        srcstring = 'source={}'.format(source['id'])
        srtstring = '&sortBy={}'.format(source['sortBysAvailable'][0])
    else:
        print('using {}'.format(source))
        srt='latest'
        for k in sourceList:
            if k['id'] == source:
                srt=k['sortBysAvailable'][0]
        srtstring='&sortBy={}'.format(srt)
        # TODO: check source exists and also sort is valid
        srcstring='source={}'.format(source)


    urlstring=newsapi + 'articles?' + srcstring + srtstring + '&apiKey=' + key #+ country + language
    print("calling: {}".format(urlstring))
    url = requests.get(urlstring)
    titles=[]
    articles=[]
    bl=json.loads(url.text)
    xx=add_records(db,bl)
    if ttls != None and ttls.upper()=='Y':
        for l in bl['articles']:
            titles.append(l['title'])
        return json.dumps(titles)
    return json.dumps(bl['articles'])



def add_records(coll,recs):
    rvs=[]
    if 'articles'  in recs:
        for r in recs['articles']:
            x=ids(r['url'])
            xd =x.hexdigest()
            r['_id']=xd
            if not coll.find_one({'_id':xd}):
                print("adding... {}".format(r['title']))
                coll.insert_one(r)
            else:
                print('{} already there'.format(xd))
    return 0
#    ids= coll.insert_many(recs)
#    return ids


# Init Host
if __name__=='__main__':
    print("initalising...")
    port=args.port
    sourceList=get_sources()
    print('sources acquired:')

    app.run(host='::', port=port)
