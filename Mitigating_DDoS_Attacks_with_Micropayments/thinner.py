import sys
import json
import time
import socket
from threading import Thread
from web3 import Web3
from heapq import heappop, heappush

global thinner_entries
global request_queue

def run_auction(w3, wallet_address, contract, wallet_private_key, sock, capacity):
    global request_queue
    while True:
        if not request_queue:
            continue
        winner = heappop(request_queue)
        # Send requested resource and deduct from user's balance
        print("Winning bid, deducting {} from address {}".format(winner[0], winner[1]))
        sock.sendto("The Magic Words are Squeamish Ossifrage".encode(), winner[2])
        deduct_from_balance(w3, wallet_address, contract, w3.toChecksumAddress("0x" + winner[1]), winner[0], wallet_private_key)
        thinner_entries[winner[1]][0] -= winner[0]
        # Pop from queue every 1/C seconds
        time.sleep(1/capacity)

# If a new account is added store info in table
def handle_event(event):
    global thinner_entries
    # Get address, bal, bid and pub key of new entries to smart contract and add to thinner
    s = event['data']
    addr = s[26:66]
    bal = int(s[66:130], 16)
    bid = int(s[130:194], 16)
    chal = s[194:]
    thinner_entries[addr] = [bal, bid, chal]
    print("New entry added- addr: {} bal: {} bid: {} chal: {}".format(addr, bal, bid, chal))

# Continuously check whether a new account has been added to the smart contract
def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
            time.sleep(poll_interval)

# Execute thinner logic
def process_packet(payload, address, sock):
    global thinner_entries
    global request_queue
    cutoff = 5
    print("Processing packet from {}".format(address))
    if len(payload) < 20:
        print("Malformed packet")
        sock.sendto("The server is currently auctioning off capacity, please bid for service using the following "
                    "smart contract: 0x1e98718ec3b5a5409c6e8901679cad975a7cae2c".encode(), address)
        return
    addr = (payload[0:20]).hex()
    # check if address is valid
    if addr not in thinner_entries:
        print("Address not in table")
        sock.sendto("The server is currently auctioning off capacity, please bid for service using the following "
                    "smart contract: 0x1e98718ec3b5a5409c6e8901679cad975a7cae2c".encode(), address)
        return
    # check if H(password) = challenge
    if not thinner_entries[addr][2] == Web3.sha3(payload[20:]).hex()[2:]:
        print("Invalid password")
        sock.sendto("Invalid password".encode(), address)
        return
    bid = thinner_entries[addr][1]
    # check if balance is sufficient
    if thinner_entries[addr][0] < bid:
        print("Insufficient balance")
        sock.sendto("Insufficient balance".encode(), address)
        return
    # Inform client theyve been added to queue
    print("Adding to queue")
    sock.sendto("You've been added to the auction queue".encode(), address)
    heappush(request_queue, (bid, addr, address))
    return

# Function that calls deductFromBalance in smart contract
def deduct_from_balance(w3, wallet_address, contract, customer, amount, wallet_private_key):
    nonce = w3.eth.getTransactionCount(wallet_address)
    txn_dict = contract.functions.deductFromBalance(customer, amount).buildTransaction({
            'gas': 2000000,
            'gasPrice': w3.toWei('40', 'gwei'),
            'nonce': nonce,
            'chainId': 3
    })
    signed_txn = w3.eth.account.signTransaction(txn_dict, wallet_private_key)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    txn_receipt = None
    count = 0
    while txn_receipt is None and (count < 30):

        txn_receipt = w3.eth.getTransactionReceipt(txn_hash)

        time.sleep(10)

    if txn_receipt is None:
        return {'status': 'failed', 'error': 'timeout'}

    return {'status': 'added', 'txn_receipt': txn_receipt}

def main():
    # Socket params
    IPADDR = '0.0.0.0'
    PORT = 1234
    # Capcity
    CAPACITY = 1000

    global thinner_entries
    global request_queue
    thinner_entries = dict()
    request_queue = []

    # Must be running go-ethereum testnet node: "$geth --testnet --syncmode light"
    w3 = Web3(Web3.IPCProvider("/home/ubuntu/.ethereum/testnet/geth.ipc"))

    # Specify ethereum account parameters
    wallet_private_key = '4C20CC47324645327C83F79A39CCF35FBD1DC2F8EF3192F7FF61DF924F1481EC'
    wallet_address = w3.toChecksumAddress('0xf935c6a706cb88fe748e645e10ca207d152b8987')
    contract_address = w3.toChecksumAddress('0x1e98718ec3b5a5409c6e8901679cad975a7cae2c')
    contract_abi = json.loads('[{"constant":false,"inputs":[{"name":"customer","type":"address"},{"name":"price","type":"uint256"}],"name":"deductFromBalance","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"bid","type":"uint256"},{"name":"secret","type":"uint256"}],"name":"newBidder","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"inputs":[{"name":"_sellerAddress","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"name":"_from","type":"address"},{"indexed":false,"name":"deposit","type":"uint256"},{"indexed":false,"name":"bid","type":"uint256"},{"indexed":false,"name":"secret","type":"uint256"}],"name":"Deposit","type":"event"}]')
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IPADDR, PORT))

    # Create filter that looks for contract_address in new blocks and enter loop
    block_filter = w3.eth.filter({'fromBlock':'latest', 'address':contract_address})
    worker1 = Thread(target=log_loop, args=(block_filter, 5), daemon=True)
    worker1.start()

    # Initialize thread that pops from request queue every 1/C seconds
    worker2 = Thread(target=run_auction, args=(w3, wallet_address, contract, wallet_private_key, sock, CAPACITY), daemon=True)
    worker2.start()

    try:
        while True:
            payload, address = sock.recvfrom(8192)
            process_packet(payload, address, sock)
    except KeyboardInterrupt:
        sock.close()
        sys.exit()

main()
