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
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash 
from pymongo import MongoClient 
import datetime, time, os
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

print("pymongo started")



# Init our db in all places
def init_db():
    client = MongoClient()
    cl = client.newsstand
    print('yeah baby')
    return cl.articles

db = init_db()

app = Flask(__name__)

# 21.co wallet & payment
# Init Flask, Wallet and Payment
print("skipping wallet for debug porpoises")
#print("Initiating wallet stuff")
#wallet = Wallet()
#payment = Payment(app, wallet)
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
@app.route('/index.html')
def main():
    nw=datetime.datetime.now()
    hrs=datetime.timedelta(hours=1)
    after=nw - hrs
    #rows=db.find({'date':{'$gt':after}})
    return render_template('index.html')

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


# Init Host
if __name__=='__main__':
    # TODO: Remove the  threaded daemon and put it in it's own file
    # TODO: Wrap this in a loop &/or generate a config
    # file if none exists

    print("initalising...")
    app.run(host='::', port=port)
