import time
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import hashlib

class CmpETransaction:

    def __init__(self, fromAdr, toAdr, amount):
        self.fromAddress = fromAdr
        self.toAdr = toAdr
        self.amount = amount
        self.timestamp = time.time()
        self.signature = None
    
    def __repr__(self):
        return str(self.fromAddress) + str(self.toAdr) + str(self.amount) + str(self.timestamp)

    def log(self):
        if self.fromAddress != None:
            return {"fromAdr": str(self.fromAddress.hex()[:10]), "toAdr": str(self.toAdr.hex()[:10]), "amount": str(self.amount), "time": str(self.timestamp)}
        else:
            return {"fromAdr": "None", "toAdr": str(self.toAdr.hex()[:10]), "amount": str(self.amount), "time": str(self.timestamp)}

    def calculateTransactionHash(self):
        return hashlib.sha256(self.toString().encode('utf-8'))
        

    def signTransaction(self, secretKey):
        sk2 = SigningKey.from_string(secretKey, curve=SECP256k1)
        self.signature = sk2.sign(self.calculateTransactionHash().digest())


    def isTransactionValid(self, publicKey):
        vk = VerifyingKey.from_string(publicKey, curve=SECP256k1)
        try:
            vk.verify(self.signature, self.calculateTransactionHash().digest())
            return True
        except:
            return False

    def toString(self):
        return str(self.fromAddress) + str(self.toAdr) + str(self.amount) + str(self.timestamp)

# if __name__ == "__main__":
#     sk = SigningKey.generate(curve=SECP256k1)
#     vk = sk.verifying_key

#     sk_string = sk.to_string()
#     vk_string = vk.to_string()

#     sk2 = SigningKey.generate(curve=SECP256k1)
#     vk2 = sk2.verifying_key

#     sk_string2 = sk2.to_string()
#     vk_string2 = vk2.to_string()

#     a = CmpETransaction("src", "dst", 10000)

#     print(a.calculateTransactionHash())

#     a.signTransaction(sk_string)

#     print(a.signature)

#     print(a.isTransactionValid(vk_string))