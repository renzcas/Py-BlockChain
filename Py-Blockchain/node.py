#node.py — Flask blockchain node (single node, wallets + signing)

from flask import Flask, request, jsonify
import hashlib
import json
import time
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError

app = Flask(__name__)

# ---------- Wallet / Keys / Addresses ----------

class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    @property
    def address(self):
        pub_bytes = self.public_key.to_string()
        sha = hashlib.sha256(pub_bytes).digest()
        ripe = hashlib.new("ripemd160", sha).hexdigest()
        return ripe

    def sign(self, message: str) -> str:
        signature = self.private_key.sign(message.encode())
        return signature.hex()

    def export(self):
        return {
            "private_key": self.private_key.to_string().hex(),
            "public_key": self.public_key.to_string().hex(),
            "address": self.address
        }


def verify_signature(public_key_hex: str, message: str, signature_hex: str) -> bool:
    try:
        pub_bytes = bytes.fromhex(public_key_hex)
        vk = VerifyingKey.from_string(pub_bytes, curve=SECP256k1)
        vk.verify(bytes.fromhex(signature_hex), message.encode())
        return True
    except (BadSignatureError, ValueError):
        return False


def pubkey_to_address(public_key_hex: str) -> str:
    pub_bytes = bytes.fromhex(public_key_hex)
    sha = hashlib.sha256(pub_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).hexdigest()
    return ripe


# ---------- Block / Blockchain ----------

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


class Blockchain:
    def __init__(self, difficulty=3):
        self.unconfirmed_transactions = []
        self.chain = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            transactions=["Genesis Block"],
            timestamp=time.time(),
            previous_hash="0"
        )
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def create_transaction_message(self, sender, recipient, amount, timestamp):
        tx_core = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "timestamp": timestamp
        }
        return json.dumps(tx_core, sort_keys=True)

    def add_signed_transaction(self, sender_pubkey_hex, recipient_address, amount, signature_hex, timestamp=None):
        if timestamp is None:
            timestamp = time.time()

        sender_address = pubkey_to_address(sender_pubkey_hex)
        message = self.create_transaction_message(
            sender=sender_address,
            recipient=recipient_address,
            amount=amount,
            timestamp=timestamp
        )

        if not verify_signature(sender_pubkey_hex, message, signature_hex):
            return False, "Invalid signature"

        tx = {
            "sender_address": sender_address,
            "sender_pubkey": sender_pubkey_hex,
            "recipient_address": recipient_address,
            "amount": amount,
            "timestamp": timestamp,
            "signature": signature_hex
        }

        self.unconfirmed_transactions.append(tx)
        return True, "Transaction added"

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        target_prefix = "0" * self.difficulty

        while not computed_hash.startswith(target_prefix):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        return (block_hash.startswith("0" * self.difficulty)
                and block_hash == block.compute_hash())

    def mine(self, miner_address=None, reward_amount=1):
        if not self.unconfirmed_transactions:
            return None, "No transactions to mine"

        if miner_address is not None:
            reward_tx = {
                "sender_address": "NETWORK",
                "sender_pubkey": None,
                "recipient_address": miner_address,
                "amount": reward_amount,
                "timestamp": time.time(),
                "signature": None
            }
            self.unconfirmed_transactions.append(reward_tx)

        new_block = Block(
            index=len(self.chain),
            transactions=self.unconfirmed_transactions.copy(),
            timestamp=time.time(),
            previous_hash=self.last_block.hash
        )

        proof = self.proof_of_work(new_block)
        added = self.add_block(new_block, proof)

        if added:
            self.unconfirmed_transactions = []
            return new_block, "Block mined"
        else:
            return None, "Failed to add block"

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]

            if curr.previous_hash != prev.hash:
                return False

            if curr.hash != curr.compute_hash():
                return False

            if not curr.hash.startswith("0" * self.difficulty):
                return False

            for tx in curr.transactions:
                if tx == "Genesis Block":
                    continue
                if tx["sender_address"] == "NETWORK":
                    continue

                sender_pubkey_hex = tx["sender_pubkey"]
                signature_hex = tx["signature"]

                msg = self.create_transaction_message(
                    sender=tx["sender_address"],
                    recipient=tx["recipient_address"],
                    amount=tx["amount"],
                    timestamp=tx["timestamp"]
                )

                if not verify_signature(sender_pubkey_hex, msg, signature_hex):
                    return False

        return True

    def balance_of(self, address):
        balance = 0
        for block in self.chain:
            if block.index == 0:
                continue
            for tx in block.transactions:
                if tx == "Genesis Block":
                    continue
                if tx["sender_address"] == address:
                    balance -= tx["amount"]
                if tx["recipient_address"] == address:
                    balance += tx["amount"]
        return balance


blockchain = Blockchain()


# ---------- Flask Endpoints ----------

@app.route("/wallet/new", methods=["GET"])
def wallet_new():
    wallet = Wallet()
    return jsonify(wallet.export()), 200


@app.route("/transaction/new", methods=["POST"])
def transaction_new():
    data = request.get_json()
    required = ["sender_pubkey", "recipient_address", "amount", "signature", "timestamp"]
    if not all(k in data for k in required):
        return jsonify({"message": "Missing fields"}), 400

    ok, msg = blockchain.add_signed_transaction(
        sender_pubkey_hex=data["sender_pubkey"],
        recipient_address=data["recipient_address"],
        amount=data["amount"],
        signature_hex=data["signature"],
        timestamp=data["timestamp"]
    )

    status = 201 if ok else 400
    return jsonify({"message": msg}), status


@app.route("/mine", methods=["GET"])
def mine():
    miner_address = request.args.get("miner_address", default=None, type=str)
    block, msg = blockchain.mine(miner_address=miner_address)

    if block is None:
        return jsonify({"message": msg}), 400

    return jsonify({
        "message": msg,
        "index": block.index,
        "hash": block.hash,
        "previous_hash": block.previous_hash,
        "nonce": block.nonce,
        "transactions": block.transactions
    }), 200


@app.route("/chain", methods=["GET"])
def full_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "nonce": block.nonce,
            "transactions": block.transactions
        })
    return jsonify({
        "length": len(chain_data),
        "chain": chain_data,
        "valid": blockchain.is_chain_valid()
    }), 200


@app.route("/pending", methods=["GET"])
def pending():
    return jsonify(blockchain.unconfirmed_transactions), 200


@app.route("/balance/<address>", methods=["GET"])
def balance(address):
    bal = blockchain.balance_of(address)
    return jsonify({"address": address, "balance": bal}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
