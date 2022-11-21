import config, time, ccxt, hideData
from datetime import date
from flask import Flask, render_template, request, flash, redirect, url_for, make_response ,jsonify
import mysql.connector
from flask_cors import CORS
from web3 import Web3
import requests
import json
import smtplib
from solcx import compile_source
from web3.gas_strategies.rpc import rpc_gas_price_strategy


app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'somerandomstring'
app.config["JSON_AS_ASCII"] = False
CORS(app)

w3 = Web3(Web3.HTTPProvider(hideData.MAINNET_ETH)).eth
wCheck = Web3(Web3.HTTPProvider(hideData.MAINNET_ETH))

# get transactions in specific address
class GetDataAPI():
    def __init__(self, address, apikey, typeOf):
        self.address = address
        self.apiKey = apikey
        self.typeOf = typeOf
    
    def getDataAddress(self):
        addressData = []
        API = f"https://api.etherscan.io/api?module=account&action=txlist&address={self.address}&startblock=0&endblock=99999999&page=1&offset=10&sort=asc&apikey={self.apiKey}&fbclid"
        data = requests.get(API)
        for i in range(10):
            addressData.append(json.loads(data.text)["result"][i][self.typeOf])
        
        return addressData

# connect my sql
def connectDatabase():
    return mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "",
        db = "reports"
    )

def showData():
    mydb = connectDatabase()
    myCursor = mydb.cursor(dictionary=True)
    myCursor.execute("SELECT * FROM data")
    myResult = myCursor.fetchall()

    return myResult

# will wrap by try except
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

    # hash, block, from and to in address
    totalHash = GetDataAPI(address, hideData.API_KEY, "hash")
    totalBlockNumber = GetDataAPI(address, hideData.API_KEY, "blockNumber")
    totalFrom = GetDataAPI(address, hideData.API_KEY, "from")
    totalTo = GetDataAPI(address, hideData.API_KEY, "to")

    # render to address page
    return render_template(
        'address.html',
        ethPrice = ethPrice,
        address = address,
        balance = balance,
        totalSupply = totalSupply,
        totalHash = totalHash.getDataAddress(),
        totalBlockNumber = totalBlockNumber.getDataAddress(),
        totalFrom = totalFrom.getDataAddress(),
        totalTo = totalTo.getDataAddress()
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
                myResult = showData()
            )

        else:
            flash('Only Admin', 'danger')
            return redirect('/')

# send ether to someone only admin
@app.route("/sendEther", methods=["POST"])
def sendEther():
    addressTo = request.form["address"]
    amountTo = request.form["amount"]

    w3 = Web3(Web3.HTTPProvider(hideData.GORLI))

    account_from = {
        "private_key": hideData.PRIVATE_KEY,
        "address": hideData.ADDRESS,
    }
    address_to = addressTo

    print(
        f'Attempting to send transaction from { account_from["address"] } to { address_to }'
    )

    w3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

    tx_create = w3.eth.account.sign_transaction(
        {
            "nonce": w3.eth.get_transaction_count(account_from["address"]),
            "gasPrice": w3.eth.generate_gas_price(),
            "gas": 21000,
            "to": address_to,
            "value": w3.toWei(amountTo, "ether"),
        },
        account_from["private_key"],
    )

    tx_hash = w3.eth.send_raw_transaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Transaction successful with hash: { tx_receipt.transactionHash.hex() }")

    return redirect("/login")

# render contact route
@app.route('/contact')
def contactPage():
    return render_template('contact.html')

# render deploy route
@app.route('/deploy')
def deployPage():
    return render_template('deploy.html')

# add data to database but some error from user
@app.route('/report', methods=["POST"])
def report():
    email = request.form["email"]
    report = request.form["problem"]

    print(email, report)

    # send data to database
    mydb = connectDatabase()
    mycursor = mydb.cursor(dictionary=True)
    sql = "INSERT INTO data (email, problem) VALUES (%s, %s)"
    val = (email, report)
    mycursor.execute(sql, val)
    mydb.commit()

    # show after send
    flash('Report send', 'primary')
    return redirect("/")

# route to connect api
@app.route("/api/reports")
def readApi():
    mydb = connectDatabase()
    myCursor = mydb.cursor(dictionary=True)
    myCursor.execute("SELECT * FROM data")

    myResult = myCursor.fetchall()

    # show data route after report
    return make_response(jsonify(myResult), 200)

# delete data by id
@app.route("/api/delete/<id>")
def deleteReport(id):
    mydb = connectDatabase()
    mycursor = mydb.cursor(dictionary=True)
    
    # select of the id to delete
    sql = "DELETE FROM data WHERE id = %s"
    val = (id,)
    mycursor.execute(sql, val)
    mydb.commit()

    return redirect("/login")

# get email to reply and id to delete reply
@app.route("/api/reply/<email>/<id>")
def replyReport(id, email):
    return render_template(
        "reply.html",
        id = id,
        email = email
    )

# reply to client 
@app.route("/replyToClient", methods=["POST"])
def replyToClient():
    #send email
    email = hideData.EMAIL
    password = hideData.PASSWORD
    
    # request data for send to client
    message = request.form["message"]
    to = request.form["to"]
    id = request.form["id"]
    print(to, id)

    # send email to client
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(email, password)
    server.sendmail(email, to, message)

    # after send that delete this report
    mydb = connectDatabase()
    mycursor = mydb.cursor(dictionary=True)
    
    # select of the id to delete
    sql = "DELETE FROM data WHERE id = %s"
    val = (id,)
    mycursor.execute(sql, val)
    mydb.commit()

    return redirect("/login")

# deploy just only testnet because it cheap
@app.route("/deployContract", methods=["POST"])
def deployContract():
    contractSol = request.form["contract"]
    w3 = Web3(Web3.HTTPProvider(hideData.GORLI))

    # Solidity source code
    compiled_sol = compile_source(
        f'''
            {contractSol}
        ''',
        output_values=['abi', 'bin']
    )

    # get abi and bytecode
    contract_id, contract_interface = compiled_sol.popitem()
    bytecode = contract_interface['bin']
    abi = contract_interface['abi']

    # set static account
    account_from = {
        "private_key": hideData.PRIVATE_KEY,
        "address": hideData.ADDRESS,
    }

    print(f'Attempting to deploy from account: { account_from["address"] }')

    Contract = w3.eth.contract(abi = abi, bytecode = bytecode)

    # will develop constructor
    def setContructor(*args):
        variable = len(args)
        if variable != 0:
            for i in args:
                construct_txn = Contract.constructor(i,).buildTransaction(
                    {
                        'from': account_from['address'],
                        'nonce': w3.eth.get_transaction_count(account_from['address']),
                    }
                )
            return construct_txn
        
        else:
            construct_txn = Contract.constructor().buildTransaction(
                {
                    'from': account_from['address'],
                    'nonce': w3.eth.get_transaction_count(account_from['address']),
                }
            )
            return construct_txn

    # execute and show contract after deployed
    tx_create = w3.eth.account.sign_transaction(setContructor(), account_from['private_key'])
    tx_hash = w3.eth.send_raw_transaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f'Contract deployed at address: { tx_receipt.contractAddress }')

    flash(tx_receipt.contractAddress, 'primary')
    return redirect('/')

app.run()