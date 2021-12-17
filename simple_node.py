import random
import time
from coinWallet import CmpECoinWallet
from block import CmpEBlock
from transaction import CmpETransaction
from global_vars import TAGS, key_file, val_node_count, simple_node_count, MESSAGE_TYPE, logger_node, SIMPLE, server_node

from mpi4py import MPI
import numpy as np
import threading

comm = MPI.COMM_WORLD


class Simple_Node:
    def __init__(self, address):
        self.address = address
        self.netwDispatcherAddress = 0
        self.blockchain = None
        f = open(key_file, "rb")
        keys = [[f.read(32*j) for j in range(1, 3)]
                for i in range(1 + val_node_count + simple_node_count)]
        f.close()
        self.myWallet = CmpECoinWallet()
        self.myWallet.initWallet(keys[address])
        self.meanTransactionInterDuration = 2
        self.meanTransactionAmount = 2
        self.listenQForValidatedBlocksFromNetwDispatcher = None
        self.simpleNodeAddresses = {}
        self.run_simple_node()

    def joinCmpeCoinNetw(self):
        """
            Sends a message to network dispatcher with a tag of join request and data of its own adress.
        """
        comm.isend([self.address, self.myWallet.getPublicKey()],
                   dest=self.netwDispatcherAddress, tag=TAGS.JOIN_REQUEST)
        # Sending log message
        message = {}
        message["type"] = MESSAGE_TYPE.JOIN_SIMPLE
        message["node_type"] = SIMPLE
        message["node_address"] = self.address
        message["wallet"] = self.myWallet.log()
        comm.isend(message, dest=logger_node, tag=TAGS.JOIN_REQUEST)

    def handleReceivedValidatedBlock(self, block_info):
        block = block_info["block"]
        sender_node = block_info["sender_node"]
        hasValidTxs = block.hasValidTransactions()
        isSamePrevBlock = block.prev_block_hash == self.blockchain.chain[-1].curr_block_hash
        isSameBlock = block.calculateCurrBlockHash(
            block.proofOfWork) == block.curr_block_hash

        message = {}
        if isSamePrevBlock and hasValidTxs and isSameBlock:
            self.blockchain.chain.append(block)
            message["type"] = MESSAGE_TYPE.VAL_BLOCK
            self.myWallet.setCurrentBalance(
                self.blockchain.getBalanceOf(self.myWallet.publicKey))
            print(
                f"( Simple node rank {self.address} ) and balance is {self.blockchain.getBalanceOf(self.myWallet.publicKey)}")
        else:
            message["type"] = MESSAGE_TYPE.REJECTED_VAL_BLOCK

        # Sending log message
        message["node_type"] = SIMPLE
        message["node_address"] = self.address
        message["wallet"] = self.myWallet.log()
        message["val_block"] = block.log()
        message["sender_node"] = sender_node
        comm.isend(message, dest=logger_node, tag=TAGS.VAL_BLOCK)

    def __doRandomTransactions(self):
        """
            Sends random transactions to randomly selected simple nodes with random intervals.
        """
        while True:
            choices = [address for address in self.simpleNodeAddresses.values() if address !=
                       self.myWallet.getPublicKey()]
            # Pick a random destination
            if len(choices) == 0:
                # Wait for some time for other nodes to join
                time.sleep(0.1)
                continue
            dest_address = random.choice(choices)

            # Pick a random transaction amount
            trx_amount = np.random.exponential(self.meanTransactionAmount)

            # Create a transaction
            trx = CmpETransaction(
                self.myWallet.getPublicKey(), dest_address, trx_amount)
            trx.signTransaction(self.myWallet.getPrivateKey())
            # print(f"Simple node with address: {self.address} sending transaction:", trx)

            # Send the transaction
            comm.isend([trx, self.address],
                       dest=self.netwDispatcherAddress, tag=TAGS.NEW_TRX)
            # Sending log message
            message = {}
            message["type"] = MESSAGE_TYPE.NEW_TRX
            message["node_type"] = SIMPLE
            message["node_address"] = self.address
            message["wallet"] = self.myWallet.log()
            message["trx"] = trx.log()
            comm.isend(message, dest=logger_node, tag=TAGS.NEW_TRX)
            # Sleep for a random amount of time
            sleep_duration = np.random.exponential(
                self.meanTransactionInterDuration)
            time.sleep(sleep_duration)

    def startSendingRandomTransactions(self):
        t = threading.Thread(target=self.__doRandomTransactions)
        t.start()

    def doRandomInvalidTransaction(self):
        # TODO: Decide when this function will be called

        # Pick a random destination
        if len(self.simpleNodeAddresses) == 0:
            return

        dest_address = random.choice(
            [address for address in self.simpleNodeAddresses.values() if address != self.myWallet.getPublicKey()])
        # dest_node = random.randint(0, len(self.simpleNodeAddresses)-1)
        # dest_address = self.simpleNodeAddresses[dest_node]

        # Create an invalid transaction
        trx = CmpETransaction(self.myWallet.getPublicKey(
        ), dest_address, self.myWallet.getCurrentBalance() + 100)
        trx.signTransaction(self.myWallet.getPrivateKey())

        # Send the transaction
        comm.isend(trx, dest=self.netwDispatcherAddress, tag=TAGS.NEW_TRX)

    def handleReceivedBlockchain(self, blockchain):
        if blockchain.isChainValid():
            self.blockchain = blockchain
            self.myWallet.setCurrentBalance(
                blockchain.getBalanceOf(self.myWallet.getPublicKey()))
            message = {}
            message["type"] = MESSAGE_TYPE.BLOCKCHAIN
            message["node_type"] = SIMPLE
            message["node_address"] = self.address
            message["wallet"] = self.myWallet.log()
            message["blockChain"] = blockchain.log()
            comm.isend(message, dest=logger_node, tag=TAGS.BLOCKCHAIN)
        else:
            comm.isend(self.address, dest=self.netwDispatcherAddress,
                       tag=TAGS.BLOCKCHAIN_REQUEST)

    def handleTrxFromAPI(self, data):
        sender_node = data["sender_node"]
        receiver_node = data["receiver_node"]

        sender_address = self.simpleNodeAddresses[sender_node]
        receiver_address = self.simpleNodeAddresses[receiver_node]

        paid_amount = data["paid_amount"]

        trx = CmpETransaction(sender_address, receiver_address,
                              paid_amount)
        trx.signTransaction(self.myWallet.getPrivateKey())

        # TODO Should I put self.address or the transaction's sender address
        # Send the transaction
        comm.isend([trx, self.address],
                   dest=self.netwDispatcherAddress, tag=TAGS.NEW_TRX)

        # Sending log message
        # TODO We will need to change the logs as well
        message = {}
        message["type"] = MESSAGE_TYPE.NEW_TRX
        message["node_type"] = SIMPLE
        message["node_address"] = self.address
        message["wallet"] = self.myWallet.log()
        message["trx"] = trx.log()
        comm.isend(message, dest=logger_node, tag=TAGS.NEW_TRX)

    def run_simple_node(self):
        # Create communication channels
        listened_topics = []
        listened_topics.append(comm.irecv(source=0, tag=TAGS.BLOCKCHAIN))
        listened_topics.append(comm.irecv(source=0, tag=TAGS.VAL_BLOCK))
        listened_topics.append(comm.irecv(source=0, tag=TAGS.SIMPLE_NODE))
        listened_topics.append(comm.irecv(
            source=server_node, tag=TAGS.TRX_FROM_API))

        # Join to the network
        self.joinCmpeCoinNetw()

        # begin to send random transactions
        self.startSendingRandomTransactions()

        # Start listening for messages
        while True:
            for_check = [req.test() for req in listened_topics]

            for i, req in enumerate(for_check):
                (finished, data) = req
                if finished:
                    if i == 0:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.BLOCKCHAIN)
                        self.handleReceivedBlockchain(data)
                    elif i == 1:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.VAL_BLOCK)
                        self.handleReceivedValidatedBlock(data)
                    elif i == 2:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.SIMPLE_NODE)
                        self.simpleNodeAddresses = data
                    elif i == 3:
                        listened_topics[i] = comm.irecv(
                            source=server_node, tag=TAGS.TRX_FROM_API)
                        self.handleTrxFromAPI(data)
