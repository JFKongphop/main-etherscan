import config, time, ccxt
from flask import Flask, render_template, request, flash, redirect, url_for
from web3 import Web3


app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'somerandomstring'

w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/27543c9fa7ab46a79c091fcd44e7df02")).eth
wCheck = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/27543c9fa7ab46a79c091fcd44e7df02"))

def getEthPrice():
    price = ccxt.binance()
    ethPrice = price.fetch_ticker("ETH/USDT")

    return ethPrice

@app.route("/")
def index():
    #eth = w3.eth
    ethPrice = getEthPrice()
    latestBlocks = []
    latestTransactions = []

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
        latestTransactions = latestTransactions
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
    balance = w3.get_balance(address) / 1000000000000000000

    # render to address page
    return render_template(
        'address.html',
        ethPrice = ethPrice,
        address = address,
        balance = balance
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


app.run()