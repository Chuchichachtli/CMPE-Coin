from mpi4py import MPI
import asyncio
import websockets
import json
from global_vars import TAGS , val_node_count, simple_node_count, difficulty, time_interval, MESSAGE_TYPE

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


class CmpECoinLogger:
    message_queue = asyncio.Queue()

    def __init__(self):
        # Add
        loop = asyncio.get_event_loop()
        start_server = websockets.serve(self.listen_websocket, "localhost", 5000)
        loop.run_until_complete(start_server)
        loop.create_task(self.listen_mpi())
        loop.run_forever()

    async def listen_websocket(self, websocket, path):
        # Wait for client to send first ws connection
        await websocket.recv()

        # Listen for message queue and send to client
        while True:
            data_list = await self.message_queue.get()
            for data in data_list:
                # Wait for 0.1 seconds to ensure that all elements in the queue are sent
                await asyncio.sleep(0.1)
                response_json = json.dumps(data)
                await websocket.send(response_json)

    async def listen_mpi(self):
        # open initial receive requests opened
        listened_topics = []
        r_i_dict = {}

        old_size = len(listened_topics)
        for i in range(1,val_node_count+1):# FOR VALIDATORS  --> NEW_TRX - LOG - BLOCKCHAIN_REQUEST
            # (0 5 10) (1 6 11) (2 7 12) (3 8 13) (4 9 14) 1 2 3 
            listened_topics.append(comm.irecv(source=i, tag = TAGS.BLOCKCHAIN))
            listened_topics.append(comm.irecv(source=i, tag = TAGS.VAL_BLOCK))
            listened_topics.append(comm.irecv(source=i, tag = TAGS.NEW_TRX))
            listened_topics.append(comm.irecv(source=i, tag = TAGS.LOG))
            listened_topics.append(comm.irecv(source=i, tag = TAGS.BLOCKCHAIN_REQUEST))
            new_size = len(listened_topics)
            for j in range(old_size, new_size):
                r_i_dict[j] = i 
            old_size = new_size
        for i in range(val_node_count+1, size-1):# FOR SIMPLE (6 9 12) (7 10 13) (8 11 14)  4 - 5 - 6
            # (8 11 14 17) (9 12 15 18) (10 13 16 19) 5 - 6 - 7 - 8 
            listened_topics.append(comm.irecv(source=i, tag = TAGS.NEW_TRX))
            listened_topics.append(comm.irecv(source=i, tag = TAGS.VAL_BLOCK))
            listened_topics.append(comm.irecv(source=i, tag = TAGS.BLOCKCHAIN))
            new_size = len(listened_topics)
            for j in range(old_size, new_size):
                r_i_dict[j] = i 
            old_size = new_size
        for i in range(1,size-1):#For join requests 15-16-17  18-19-20
            listened_topics.append(comm.irecv(source= i, tag= TAGS.JOIN_REQUEST))
            r_i_dict[old_size] = i 
            old_size = len(listened_topics)

        mod_ = val_node_count * 5 % 3 
        # TODO: Change this while loop to start listening for MPI messages
        while True:
            for_check = [req.test() for req in listened_topics]

            received_data = []

            for i,req in enumerate(for_check):
                (finished, data) = req
                if finished:
                    if i < val_node_count*5: # Message coming from Validators
                        if i % 5 == 0:# send current blockhain
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.BLOCKCHAIN)
                        elif i % 5 == 1:# send current blockhain
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.VAL_BLOCK)
                        elif i % 5 == 2:# send current blockhain
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.NEW_TRX)
                        elif i % 5 == 3:# send current blockhain
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.LOG)
                        elif i % 5 == 4:# send latest validated block
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.BLOCKCHAIN_REQUEST)
                    elif i < val_node_count * 5 + simple_node_count * 3: # Message coming from Simples, Transaction request
                        if i % 3 == mod_:
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.NEW_TRX)
                        elif i % 3 == (mod_+1) % 3:
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.VAL_BLOCK)
                        else:
                            listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.BLOCKCHAIN)
                    else: # For join requests
                        listened_topics[i] = comm.irecv(source = r_i_dict[i], tag = TAGS.JOIN_REQUEST)

                    received_data.append(data)

            # print("Logger received", data)
            await self.message_queue.put(received_data)
            await asyncio.sleep(0.0001)
