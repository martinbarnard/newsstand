#     _   __                       __                  __
#    / | / /__ _      ____________/ /_____ _____  ____/ /
#   /  |/ / _ \ | /| / / ___/ ___/ __/ __ `/ __ \/ __  / 
#  / /|  /  __/ |/ |/ (__  |__  ) /_/ /_/ / / / / /_/ /  
# /_/ |_/\___/|__/|__/____/____/\__/\__,_/_/ /_/\__,_/   
                                                       
# Description: Provides the latest news from a multitude of news sources.
# GitHub Repository: Newsstand (github.com/cryptopelago/newsstand)
# License: Unlicense (unlicense.org)


# Load libraries
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash 
from pymongo import *
import datetime, time, os, json
import dateutil.parser
from random import choice

# 21co wallet 
### We are skipping until we can sort out the app
#print('importing two1 stuff')
#from two1.wallet import Wallet
#from two1.bitserv.flask import Payment
#
# Our daemon should be running separately as it purely concerns itself with populating our db
#from daemon import *
# 

from config import *

print("newstand starting...")



# Init our db in all places
def init_db():
    client = MongoClient()
    cl = client.newsstand
    print('yeah baby')
    return cl.articles

def get_sources():
    '''
    Will return our sources
    '''
    client = MongoClient()
    cl=client.newsstand
    cl = cl.sources
    res=cl.find()
    rvs=[]
    for r in res:
        rvs.append(r)
    return rvs



db = init_db()

app = Flask(__name__, template_folder='templates')

# 21.co wallet & payment
# Init Flask, Wallet and Payment
print("skipping wallet for debug porpoises")
#print("Initiating wallet stuff")
#wallet = Wallet()
#payment = Payment(app, wallet)
#print("Wallet initiated")

# our list of sources
sourceList=get_sources()

# TODO: 
# nltk keywords extraction
# api to twitter sentiment analysis

################################################################################
# Routed functions
################################################################################

@app.route('/')
def index():
    global categories, sourceList
    nw=datetime.datetime.now()
    hrs=datetime.timedelta(hours=9)
    after=nw - hrs
    return render_template('index.html', rows=None, flt=None, categories=categories, sources=sourceList, request=request)

@app.route('/sources')
def sources():
    '''
    Display a list of sources
    '''
    rval=[]
    sourceList = get_sources()
    for s in sourceList:
        rval.append(s['id'])
    return json.dumps(rval)
@app.route('/news', methods=['GET', 'POST'])
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
    global categories, sourceList
    if request.method=='GET':
        source      = request.args.get('source','all')
        cats= request.args.get('category', 'all')
        author      = request.args.get('author', 'all')
        latest      = request.args.get('latest', '1')
    elif request.method=='POST':
        source      = request.form.get('source','all')
        cats  = request.form.get('category', 'all')
        author      = request.form.get('author', 'all')
        latest      = request.form.get('latest', '1')

    # fields here...
    nw=datetime.datetime.now()
    hrs=datetime.timedelta(hours=1)
    after=nw - hrs
    rv=['{}'.format(source)]
    #flt={'date':{'$gt':after}}
    flt={}
    if source != 'all' and source != '':
        flt['src'] = source.replace(' ', '-')
    if  cats != 'all' and cats != '':
        flt['category'] = cats.lower()
    if author  != 'all' and author != '':
        flt['author'] = author
    # latest overrides all the others
    if  latest == 1:
        flt={}


    print('filter {}'.format(flt))
    rows=db.find(flt).sort('date', DESCENDING).limit(50)
    if rows:
        for row in rows:
            k={}
            # todo omit key of date
            for r in row.keys():
                if r!='date':
                    k[r]=row[r]
                else:
                    k[r]=row[r].strftime('%Y-%m-%d %H:%M')
            rv.append(k)
    return render_template('index.html', rows=rv[1:],flt=flt, categories=categories, sources=sourceList, request=request)
            #return json.dumps(rv[1:])




################################################################################
# private functions
################################################################################


# Init Host
if __name__=='__main__':
    # TODO: Remove the  threaded daemon and put it in it's own file
    # TODO: Wrap this in a loop &/or generate a config
    # file if none exists

    print("initalising...")
    app.run(host='::', port=port, debug=True)
