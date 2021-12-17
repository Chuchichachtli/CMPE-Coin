# transaction.py

import pytest
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from transaction import CmpETransaction

def test_verify_success():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.verifying_key

    sk_string = sk.to_string()
    vk_string = vk.to_string()

    trx1 = CmpETransaction("src", "dst", 10000)
    trx1.signTransaction(sk_string)

    assert trx1.isTransactionValid(vk_string) == True


def test_verify_failure():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.verifying_key

    sk_string = sk.to_string()
    vk_string = vk.to_string()

    sk2 = SigningKey.generate(curve=SECP256k1)
    vk2 = sk2.verifying_key

    sk_string2 = sk2.to_string()
    vk_string2 = vk2.to_string()

    trx1 = CmpETransaction("src", "dst", 10000)

    trx1.signTransaction(sk_string)

    assert trx1.isTransactionValid(vk_string2) == False
