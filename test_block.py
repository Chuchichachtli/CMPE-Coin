from block import CmpEBlock
import time
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import hashlib
from transaction import CmpETransaction 

def test_same_hash():
    block1 = CmpEBlock("0", [])
    block2 = CmpEBlock("0", [])
    assert block1.calculateCurrBlockHash(1) == block2.calculateCurrBlockHash(1)

def test_validate_block():
    difficulty = 10
    block = CmpEBlock("0", [])
    block.validateBlock(difficulty)
    # print(str(bin(int(block.curr_block_hash, 16))[2:].zfill(256)))
    assert "0"*difficulty == str(bin(int(block.curr_block_hash, 16))[2:].zfill(256))[:difficulty]

def test_block_success():
    private_key2 = SigningKey.generate(curve=SECP256k1)
    public_key2 = private_key2.verifying_key
    txs = []
    for i in range(5):
        private_key = SigningKey.generate(curve=SECP256k1)
        public_key = private_key.verifying_key
        curr_tx = CmpETransaction(public_key.to_string(),public_key2.to_string(),0)
        curr_tx.signTransaction(private_key.to_string())
        txs.append(curr_tx)
    
    block = CmpEBlock("", txs)
    block.validateBlock(1)

    currentHash = block.curr_block_hash
    calculatedHash = block.calculateCurrBlockHash(block.proofOfWork)

    assert currentHash == calculatedHash

def test_block_failure():
    private_key2 = SigningKey.generate(curve=SECP256k1)
    public_key2 = private_key2.verifying_key
    txs = []
    for i in range(5):
        private_key = SigningKey.generate(curve=SECP256k1)
        public_key = private_key.verifying_key
        curr_tx = CmpETransaction(public_key.to_string(),public_key2.to_string(),0)
        curr_tx.signTransaction(private_key.to_string())
        txs.append(curr_tx)

    block = CmpEBlock("", txs)
    block.validateBlock(1)
    curr_tx = CmpETransaction(public_key.to_string(),public_key2.to_string(),0)
    curr_tx.signTransaction(private_key2.to_string())
    block.transactions.append(curr_tx)
    currentHash = block.curr_block_hash
    calculatedHash = block.calculateCurrBlockHash(block.proofOfWork)
    
    assert currentHash != calculatedHash

print("Running block test 1")
test_same_hash()
print("Running block test 2")
test_validate_block()
print("Running block test 3")
test_block_success()
print("Running block test 4")
test_block_failure()