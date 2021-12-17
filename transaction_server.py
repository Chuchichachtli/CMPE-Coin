import json
from mpi4py import MPI
from flask import Flask, jsonify, request, Response
from flask_cors import CORS, cross_origin
from global_vars import TAGS, val_node_count,  simple_node_count

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


class CmpeCoinTransactionServer:

    def __init__(self):
        self.run_server()

    @app.route("/add-transaction", methods=["POST"])
    @cross_origin()
    def add_transaction():
        error = {}

        try:
            transaction_node = request.json["transaction_node"]
            if type(transaction_node) != int or transaction_node < 1 or transaction_node > simple_node_count:
                error["transaction_node_error"] = "Transaction node input was faulty"
        except:
            error["transaction_node_error"] = "Need value 'transaction_node'"

        try:
            sender_node = request.json["sender_node"]
            if type(sender_node) != int or sender_node < 1 or sender_node > simple_node_count:
                error["sender_node_error"] = "Sender node input was faulty"
        except:
            error["sender_node_error"] = "Need value 'sender_node'"

        try:
            receiver_node = request.json["receiver_node"]
            if type(receiver_node) != int or receiver_node < 1 or receiver_node > simple_node_count:
                error["receiver_node_error"] = "Receiver node input was faulty"
        except:
            error["receiver__node_error"] = "Need value 'receiver_node'"

        try:
            paid_amount = request.json["paid_amount"]
            if type(paid_amount) != int or paid_amount < 0:
                error["paid_amount_error"] = "Amount paid input was faulty"
        except:
            error["paid_amount_error"] = "Need value 'paid_amount'"

        if error:
            return Response(json.dumps(error), status=400, mimetype='application/json')

        request.json["transaction_node"] += val_node_count
        request.json["receiver_node"] += val_node_count
        request.json["sender_node"] += val_node_count

        data = request.json

        comm.isend(data, dest=data["transaction_node"], tag=TAGS.TRX_FROM_API)

        return jsonify({"response":  "Transaction was successful"})

    def run_server(self):
        app.run(host="0.0.0.0", port=4567, debug=False)


if __name__ == "__main__":
    CmpeCoinTransactionServer()
