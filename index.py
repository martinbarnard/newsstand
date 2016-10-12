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
import urllib
import os
import json
import yaml
from flask import Flask, request
from two1.wallet import Wallet
from two1.bitserv.flask import Payment

# Init Flask, Wallet and Payment
app = Flask(__name__)
wallet = Wallet()
payment = Payment(app, wallet)

# Add 402
@app.route('/news')
@payment.required(900)
def lookup_string():
    source = request.args.get('source')
    key = os.environ.get('KEY')
    url = requests.get('https://newsapi.org/v1/articles?source='+source+'&sortBy=latest&apiKey='+key)
    return url.text

# Init Host
if __name__=='__main__':
    app.run(host='::', port='10125')
