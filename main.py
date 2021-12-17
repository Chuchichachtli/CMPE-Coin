from logger import CmpECoinLogger
from network_dispatcher import CmpECoinNetwDispatcher
from simple_node import Simple_Node
from validator_node import Validator_Node
from global_vars import val_node_count, simple_node_count, logger_node
from mpi4py import MPI
from transaction_server import CmpeCoinTransactionServer
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if __name__ == "__main__":

    # due to MPI requirements, types of processes assigned
    if rank == 0:
        print("Dispatcher started")
        nd = CmpECoinNetwDispatcher()
    elif rank <= val_node_count:
        time.sleep(rank * 0.25)
        print("Validator started", rank)
        vn = Validator_Node(address=rank)
    elif rank <= val_node_count+simple_node_count:
        time.sleep(1 + rank * 0.25)
        print("Simple node started", rank)
        sn = Simple_Node(address=rank)
    elif rank == logger_node:
        print("Logger node started", rank)
        ld = CmpECoinLogger()
    else:
        print("Transaction server node started", rank)
        ts = CmpeCoinTransactionServer()
