from block import CmpEBlock
import time
from typing import cast
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import hashlib
from transaction import CmpETransaction 
from blockChain import CmpEBlockchain
from global_vars import key_file, val_node_count, simple_node_count

def test_dummy_blocks():
    blockchain1 = CmpEBlockchain(1) 
    blockchain2 = CmpEBlockchain(1)

    blockchain1.createInitialDummyBlock()
    time.sleep(1)
    blockchain2.createInitialDummyBlock()
    assert blockchain1.chain[0].curr_block_hash!=blockchain2.chain[0].curr_block_hash

def test_valid_chain_success():
    f = open(key_file,"rb")
    keys = [[f.read(32*j) for j in range(1,3)] for i in range(1 + val_node_count + simple_node_count)]
    f.close()
    blockchain = CmpEBlockchain(1,keys) 
    blockchain.createInitialDummyBlock()
    private_key2 = SigningKey.generate(curve=SECP256k1)
    public_key2 = private_key2.verifying_key
    for j in range(4):
        for i in range(5):
            private_key = SigningKey.generate(curve=SECP256k1)
            public_key = private_key.verifying_key
            curr_tx = CmpETransaction(public_key.to_string(),public_key2.to_string(),0)
            curr_tx.signTransaction(private_key.to_string())
            blockchain.addTransactionToPendingList(curr_tx)
        blockchain.chain.append(blockchain.validatePendingTransactions(public_key2.to_string()))
    
    assert blockchain.isChainValid()


def test_valid_chain_failure():
    f = open(key_file,"rb")
    keys = [[f.read(32*j) for j in range(1,3)] for i in range(1 + val_node_count + simple_node_count)]
    f.close()
    blockchain = CmpEBlockchain(1,keys) 
    blockchain.createInitialDummyBlock()
    private_key2 = SigningKey.generate(curve=SECP256k1)
    public_key2 = private_key2.verifying_key
    for j in range(2):
        for i in range(5):
            private_key = SigningKey.generate(curve=SECP256k1)
            public_key = private_key.verifying_key
            curr_tx = CmpETransaction(public_key.to_string(),public_key2.to_string(),0)
            curr_tx.signTransaction(private_key.to_string())
            blockchain.addTransactionToPendingList(curr_tx)
        blockchain.chain.append(blockchain.validatePendingTransactions(public_key2))
        # Adding Extra transaction for failure
        blockchain.chain[-1].transactions.append(CmpETransaction(public_key.to_string(),public_key2.to_string(),0))    
    
    assert not blockchain.isChainValid()

print("dummy test")
test_dummy_blocks()
print("valid success test")
test_valid_chain_success()
print("valid failure test")
test_valid_chain_failure()
print("done 3/3")



