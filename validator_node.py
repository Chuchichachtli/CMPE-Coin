from blockChain import CmpEBlockchain
from block import CmpEBlock
from coinWallet import CmpECoinWallet
from global_vars import difficulty
from mpi4py import MPI
from global_vars import TAGS, key_file, val_node_count, simple_node_count, MESSAGE_TYPE, logger_node, VAL


comm = MPI.COMM_WORLD


class Validator_Node:
    def __init__(self, address):
        self.address = address
        self.netwDispatcherAddress = 0
        self.blockchain = None
        self.listenQForTransactionsFromNetwDispatcher = None
        self.listenQForValidatedBlocksFromNetwDispatcher = None
        self.listenQForValidatedBlockchain = None
        self.wallet = CmpECoinWallet()
        f = open(key_file, "rb")
        keys = [[f.read(32*j) for j in range(1, 3)]
                for i in range(1 + val_node_count + simple_node_count)]
        f.close()
        self.wallet.initWallet(keys[address])
        self.run_validator_node()

    def joinCmpeCoinNetw(self):
        """
            Sends a message to network dispatcher with a tag of join request and data of its own adress.
        """
        comm.isend([self.address, -1],
                   dest=self.netwDispatcherAddress, tag=TAGS.JOIN_REQUEST)
        # Sending log message
        message = {}
        message["type"] = MESSAGE_TYPE.JOIN_VAL
        message["node_type"] = VAL
        message["node_address"] = self.address
        message["wallet"] = self.wallet.log()
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
        else:
            message["type"] = MESSAGE_TYPE.REJECTED_VAL_BLOCK

        self.wallet.setCurrentBalance(
            self.blockchain.getBalanceOf(self.wallet.publicKey))

        # Sending log message
        message["node_type"] = VAL
        message["node_address"] = self.address
        message["wallet"] = self.wallet.log()
        message["val_block"] = block.log()
        message["sender_node"] = sender_node
        comm.isend(message, dest=logger_node, tag=TAGS.VAL_BLOCK)

    def handleReceivedTransactions(self, data):
        transaction = data[0]
        sender_node = data[1]
        message = {}
        if transaction.isTransactionValid(transaction.fromAddress):
            self.blockchain.addTransactionToPendingList(transaction)
            message["type"] = MESSAGE_TYPE.NEW_TRX
        else:
            message["type"] = MESSAGE_TYPE.NON_VALID_TRX
        # Sending log message
        message["node_type"] = VAL
        message["node_address"] = self.address
        message["wallet"] = self.wallet.log()
        message["sender_node"] = sender_node
        message["trx"] = transaction.log()
        comm.isend(message, dest=logger_node, tag=TAGS.NEW_TRX)

    def handleBeaconAndStartValidationProc(self, _message):
        # Sending log message
        message = {}
        message["type"] = MESSAGE_TYPE.BEACON
        message["node_type"] = VAL
        message["node_address"] = self.address
        message["log"] = "Beacon is received from the dispatcher."
        comm.isend(message, dest=logger_node, tag=TAGS.LOG)

        lastBlock = self.blockchain.validatePendingTransactions(
            self.wallet.getPublicKey())
        comm.isend({"block": lastBlock, "sender_node": self.address},
                   dest=self.netwDispatcherAddress, tag=TAGS.VAL_BLOCK)

        # Sending log message
        message1 = {}
        message1["type"] = MESSAGE_TYPE.BLOCK_VALIDATED
        message1["node_type"] = VAL
        message1["node_address"] = self.address
        message1["wallet"] = self.wallet.log()
        message1["val_block"] = lastBlock.log()
        message1["log"] = "Validated block is sent to the dispatcher"
        comm.isend(message1, dest=logger_node, tag=TAGS.VAL_BLOCK)

    def handleBlockchainRequest(self, new_node_address):
        if self.blockchain != None and self.blockchain.isChainValid():
            comm.isend([self.blockchain, new_node_address],
                       dest=self.netwDispatcherAddress, tag=TAGS.BLOCKCHAIN)
            message = {}
            message["type"] = MESSAGE_TYPE.BLOCKCHAIN_REQUEST
            message["node_type"] = VAL
            message["node_address"] = self.address
            message["log"] = "Blockchain is requested by the dispatcher."
            comm.isend(message, dest=logger_node, tag=TAGS.BLOCKCHAIN_REQUEST)

    def handleReceivedBlockchain(self, blockchain):
        if blockchain.isChainValid():
            self.blockchain = blockchain
            # Sending log message
            message = {}
            message["type"] = MESSAGE_TYPE.BLOCKCHAIN
            message["node_address"] = self.address
            message["wallet"] = self.wallet.log()
            message["blockChain"] = blockchain.log()
            comm.isend(message, dest=logger_node, tag=TAGS.BLOCKCHAIN)
        else:
            comm.isend(self.address, dest=self.netwDispatcherAddress,
                       tag=TAGS.BLOCKCHAIN_REQUEST)

    def run_validator_node(self):
        # Open initial receive requests
        listened_topics = []
        listened_topics.append(comm.irecv(
            source=0, tag=TAGS.BLOCKCHAIN_REQUEST))
        listened_topics.append(comm.irecv(source=0, tag=TAGS.BLOCKCHAIN))
        listened_topics.append(comm.irecv(source=0, tag=TAGS.NEW_TRX))
        listened_topics.append(comm.irecv(source=0, tag=TAGS.BEACON))
        listened_topics.append(comm.irecv(source=0, tag=TAGS.VAL_BLOCK))

        # Join to the network
        self.joinCmpeCoinNetw()

        while True:
            for_check = [req.test() for req in listened_topics]

            for i, req in enumerate(for_check):
                (finished, data) = req
                if finished:
                    if i == 0:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.BLOCKCHAIN_REQUEST)
                        self.handleBlockchainRequest(data)
                    elif i == 1:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.BLOCKCHAIN)
                        self.handleReceivedBlockchain(data)
                    elif i == 2:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.NEW_TRX)
                        self.handleReceivedTransactions(data)
                    elif i == 3:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.BEACON)
                        self.handleBeaconAndStartValidationProc(data)
                    elif i == 4:
                        listened_topics[i] = comm.irecv(
                            source=0, tag=TAGS.VAL_BLOCK)
                        self.handleReceivedValidatedBlock(data)
