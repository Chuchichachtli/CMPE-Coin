import random
from datetime import datetime
from transaction import CmpETransaction
from blockChain import CmpEBlockchain
from mpi4py import MPI
from global_vars import TAGS, key_file, val_node_count, simple_node_count, difficulty, time_interval, MESSAGE_TYPE, logger_node


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


class CmpECoinNetwDispatcher:

    def __init__(self):
        self.transxRcvQ = []
        self.validatedBlockRcvQ = []
        self.validatorNodeAddresses = []
        self.simpleNodeAddresses = {}
        self.beaconTime = datetime.now()
        self.run_dispatcher()

    def broadcastReceivedTransx(self, new_transaction):
        for i in range(1, val_node_count+1):
            comm.isend(new_transaction, dest=i, tag=TAGS.NEW_TRX)

    def broadcastLastValidatedBlock(self, new_block):
        for i in range(1, val_node_count + simple_node_count+1):
            comm.isend(new_block, dest=i, tag=TAGS.VAL_BLOCK)

    def broadcastValidationBeacon(self):
        for i in range(1, val_node_count+1):
            comm.isend("Start validation process", dest=i, tag=TAGS.BEACON)

    def sendSimpleNodeAddresses(self):
        for i in range(val_node_count+1, val_node_count+simple_node_count+1):
            comm.isend(self.simpleNodeAddresses, dest=i, tag=TAGS.SIMPLE_NODE)

    def handleNetworkJoin(self, data, type_):
        rank, new_node_address = data

        if len(self.validatorNodeAddresses) != 0:
            self.sendCurrentBlockChainRequest(rank)
            if type_ == 0:
                self.validatorNodeAddresses.append(rank)
                print(f"Newly joined node is {rank} as validator node.")
            else:
                self.simpleNodeAddresses[rank] = new_node_address
                print(f"Newly joined node is {rank} as simple node.")
                self.sendSimpleNodeAddresses()
        else:
            self.validatorNodeAddresses.append(rank)
            print(f"Newly joined node is {rank} as validator node.")
            f = open(key_file, "rb")
            keys = [[f.read(32*j) for j in range(1, 3)]
                    for i in range(1 + val_node_count + simple_node_count)]
            f.close()
            comm.isend(CmpEBlockchain(difficulty, keys),
                       dest=rank, tag=TAGS.BLOCKCHAIN)

    def sendCurrentBlockChainTo(self, blockchain, new_node_address):
        """
            Sends blockchain to newly joined node
        """
        comm.isend(blockchain, dest=new_node_address, tag=TAGS.BLOCKCHAIN)
        # print("Sent blockchain to new node", new_node_address)

    def sendCurrentBlockChainRequest(self, new_node_address):
        """
            Chooses random validator node
            Gets blockchain from validator node
            Sends blockchain to new address by broadcasting it as blockchain + target address
        """
        index = random.randint(0, len(self.validatorNodeAddresses)-1)
        validator_address = self.validatorNodeAddresses[index]
        comm.isend(new_node_address, dest=validator_address,
                   tag=TAGS.BLOCKCHAIN_REQUEST)

    def handle_new_transaction(self, data):
        self.broadcastReceivedTransx(data)

    def handle_new_block(self, block):  # message: new block
        self.broadcastLastValidatedBlock(block)

    def run_dispatcher(self):

        # open initial receive requests opened
        listened_topics = []
        for i in range(1, val_node_count+1):  # FOR VALIDATORS
            listened_topics.append(comm.irecv(source=i, tag=TAGS.BLOCKCHAIN))
            listened_topics.append(comm.irecv(source=i, tag=TAGS.VAL_BLOCK))
        for i in range(val_node_count+1, size-1):  # FOR SIMPLE
            listened_topics.append(comm.irecv(source=i, tag=TAGS.NEW_TRX))
        for i in range(1, size-1):  # For join requests
            listened_topics.append(comm.irecv(source=i, tag=TAGS.JOIN_REQUEST))

        while True:
            for_check = [req.test() for req in listened_topics]

            for i, req in enumerate(for_check):
                (finished, data) = req
                if finished:
                    if i < val_node_count*2:  # Message coming from Validators
                        if i % 2 == 0:  # send current blockhain
                            listened_topics[i] = comm.irecv(
                                source=i/2 + 1, tag=TAGS.BLOCKCHAIN)
                            self.sendCurrentBlockChainTo(data[0], data[1])
                        else:  # send latest validated block
                            listened_topics[i] = comm.irecv(
                                source=(i+1)/2, tag=TAGS.VAL_BLOCK)
                            self.handle_new_block(data)
                    elif i < val_node_count * 2 + simple_node_count:  # Message coming from Simples, Transaction request
                        listened_topics[i] = comm.irecv(
                            source=i + 1 - val_node_count, tag=TAGS.NEW_TRX)
                        self.handle_new_transaction(data)
                    else:  # For join requests
                        listened_topics[i] = comm.irecv(
                            source=i-2*val_node_count-simple_node_count, tag=TAGS.JOIN_REQUEST)
                        if i-2*val_node_count-simple_node_count > val_node_count:  # FOR SIMPLE
                            self.handleNetworkJoin(data, True)
                        else:  # FOR VALIDATORS
                            self.handleNetworkJoin(data, False)
            # Send beacons with a time interval
            current_time = datetime.now()
            if (current_time - self.beaconTime).seconds > time_interval:
                self.broadcastValidationBeacon()
                self.beaconTime = current_time
