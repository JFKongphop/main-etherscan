import config, time, ccxt, hideData
from datetime import date
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from web3 import Web3
import requests
import json
import os

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'somerandomstring'
basedir = os.path.abspath(os.path.dirname(__file__))

w3 = Web3(Web3.HTTPProvider(hideData.MAINNET_ETH)).eth
wCheck = Web3(Web3.HTTPProvider(hideData.MAINNET_ETH))
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myreport.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# create model database
class Statement(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(50),nullable=False)
    report = db.Column(db.String(300),nullable=False)

    # create database
    with app.app_context() as app:
        db.create_all()





def getEthPrice():
    price = ccxt.binance()
    ethPrice = price.fetch_ticker("ETH/USDT")

    return ethPrice

def getNode(url):
    response_API = requests.get(url)
    data = json.loads(response_API.text)
    
    return data['result']['TotalNodeCount']

def getTokenTotalSupply(address, apiKey):
    response_API = f"https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress={address}&apikey={apiKey}"
    data = requests.get(response_API)
    totalSupply = "{:,}".format(int(json.loads(data.text)["result"]) / 1000)
    
    if totalSupply != "0.0":
        return totalSupply
    else:
        return "Non-Address"


@app.route("/")
def index():
    #eth = w3.eth
    ethPrice = getEthPrice()
    latestBlocks = []
    latestTransactions = []
    nodes = getNode(hideData.API_NODE_URL)
    

    # get latest 15 blocks to show
    # get by block number and reverse from latest
    for blockNumber in range(w3.block_number, w3.block_number - 15, -1):
        eachBlock = w3.get_block(blockNumber)
        latestBlocks.append(eachBlock)

    # get latest 10 transactions to show heelo
    # get by last block and passing value to transaction and get latest 10 in this block
    for tx in latestBlocks[-1]['transactions'][-10:]:
        transaction = w3.get_transaction(tx)
        latestTransactions.append(transaction)
    
    
    # add current time to show after render by the time
    currentTime = time.time()

    # get gas price
    gasPrice = f"{w3.gas_price / 1000000000} Gwei"

    # render to index page
    return render_template(
        'index.html',
        miners = config.MINERS,
        currentTime = currentTime,
        gasPrice = gasPrice,
        ethPrice = ethPrice,
        latestBlocks = latestBlocks,
        latestTransactions = latestTransactions,
        nodes = nodes
    )

@app.route("/address")
def address():

    #get adress from input form
    address = request.args.get('address')
    ethPrice = getEthPrice()

    #chcek if have some error
    if(len(address) > 0 and len(address) < 11):
            
        # get the block number
        block = w3.get_block(int(address))

        # render to address page
        return render_template(
            "block.html",
            block = block
        )

    elif(len(address) > 50):
        # get transaction and amount of eth when click to link transaction
        tx = w3.get_transaction(address)
        value = tx.value / 1000000000000000000

        # get receipt address
        receipt = w3.get_transaction_receipt(address)
        ethPrice = getEthPrice()

        # get gas price
        gasPrice = tx.gasPrice / 1000000000000000000

        return render_template(
            "transaction.html",
            tx = tx,
            value = value,
            receipt = receipt,
            gasPrice = gasPrice,
            ethPrice = ethPrice
        )

    try:
        address = wCheck.toChecksumAddress(address)
    except:
        flash('Invalid address', 'danger')
        return redirect('/')


    # get balance from this address
    balance = str(w3.get_balance(address) / 1000000000000000000)

    # get total supply of token if it token address
    totalSupply = getTokenTotalSupply(address, hideData.API_KEY)

    # render to address page
    return render_template(
        'address.html',
        ethPrice = ethPrice,
        address = address,
        balance = balance,
        totalSupply = totalSupply
    )

@app.route("/block/<block_number>")
def block(block_number):
    
    # get the block number
    block = w3.get_block(int(block_number))

    # render to address page
    return render_template(
        "block.html",
        block = block
    )

@app.route("/transaction/<hash>")
def transaction(hash):

    # get transaction and amount of eth when click to link transaction
    tx = w3.get_transaction(hash)
    value = tx.value / 1000000000000000000

    # get receipt address
    receipt = w3.get_transaction_receipt(hash)
    ethPrice = getEthPrice()

    # get gas price
    gasPrice = tx.gasPrice / 1000000000000000000

    return render_template(
        "transaction.html",
        tx = tx,
        value = value,
        receipt = receipt,
        gasPrice = gasPrice,
        ethPrice = ethPrice
    )

# direct to login page
@app.route('/login')
def login():
    return render_template('login.html')

# get token session
@app.route('/loginAdmin', methods=["POST", "GET"])
def loginAdmin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        print(email, password)

        if not email or not password:
            return render_template(
                'login.html', 
                errorEmail = "Please-enter-email", 
                errorPassword = "Please-enter-password"
            )

        if email == "lada071159@gmail.com" and password == "123":
            return render_template(
                'admin.html',
            )
        else:
            flash('Only Admin', 'danger')
            return redirect('/')


@app.route('/contact')
def contactPage():
    return render_template('contact.html')

@app.route('/deploy')
def deployPage():
    return render_template('deploy.html')

@app.route('/report', methods=["POST"])
def report():
    email = request.form["email"]
    report = request.form["problem"]

    statement = Statement(email = email, report = report)
    db.session.add(statement)
    db.session.commit()
    print(email, report)

    flash('Message is send', 'primary')
    return redirect('/')


# more feature 
'''
    1 login admin
    2 send message to database
    3 get message to crud in admin page
    4 deploy contract by web3.py
'''

app.run()