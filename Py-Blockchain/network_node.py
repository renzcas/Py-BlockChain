#network_node.py — multi‑node Flask blockchain with consensus


from flask import Flask, request, jsonify
import hashlib
import json
import time
from urllib.parse import urlparse
import requests
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
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0, hash_value=None):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = hash_value or self.compute_hash()

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
        self.nodes = set()
        self.create_genesis_block()

    # ----- Core chain -----

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

    # ----- Transactions -----

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

    # ----- Proof of Work / Mining -----

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

    # ----- Validation -----

    def is_chain_valid(self, chain=None):
        chain = chain or self.chain

        for i in range(1, len(chain)):
            prev = chain[i - 1]
            curr = chain[i]

            if curr["previous_hash"] != prev["hash"]:
                return False

            # Rebuild block to recompute hash
            block_obj = Block(
                index=curr["index"],
                transactions=curr["transactions"],
                timestamp=curr["timestamp"],
                previous_hash=curr["previous_hash"],
                nonce=curr["nonce"]
            )
            if curr["hash"] != block_obj.compute_hash():
                return False

            if not curr["hash"].startswith("0" * self.difficulty):
                return False

            for tx in curr["transactions"]:
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

    # ----- Networking / Consensus -----

    def register_node(self, address):
        """
        address: 'http://host:port'
        """
        parsed = urlparse(address)
        self.nodes.add(f"{parsed.scheme}://{parsed.netloc}")

    def resolve_conflicts(self):
        """
        Longest valid chain rule.
        """
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            try:
                response = requests.get(f"{node}/chain")
            except requests.exceptions.RequestException:
                continue

            if response.status_code != 200:
                continue

            data = response.json()
            length = data["length"]
            chain = data["chain"]

            if length > max_length and self.is_chain_valid(chain):
                max_length = length
                new_chain = chain

        if new_chain:
            # Replace local chain
            new_chain_objs = []
            for b in new_chain:
                new_chain_objs.append(
                    Block(
                        index=b["index"],
                        transactions=b["transactions"],
                        timestamp=b["timestamp"],
                        previous_hash=b["previous_hash"],
                        nonce=b["nonce"],
                        hash_value=b["hash"]
                    )
                )
            self.chain = new_chain_objs
            return True

        return False


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

    # Broadcast new block to peers (simple: ask them to resolve)
    for node in blockchain.nodes:
        try:
            requests.get(f"{node}/nodes/resolve", timeout=2)
        except requests.exceptions.RequestException:
            pass

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
        "valid": blockchain.is_chain_valid(chain_data)
    }), 200


@app.route("/pending", methods=["GET"])
def pending():
    return jsonify(blockchain.unconfirmed_transactions), 200


@app.route("/balance/<address>", methods=["GET"])
def balance(address):
    bal = blockchain.balance_of(address)
    return jsonify({"address": address, "balance": bal}), 200


# ----- Networking endpoints -----

@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    data = request.get_json()
    nodes = data.get("nodes")
    if nodes is None or not isinstance(nodes, list):
        return jsonify({"message": "Please supply a list of nodes"}), 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({
        "message": "New nodes have been added",
        "total_nodes": list(blockchain.nodes)
    }), 201


@app.route("/nodes", methods=["GET"])
def list_nodes():
    return jsonify({"nodes": list(blockchain.nodes)}), 200


@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        message = "Our chain was replaced"
    else:
        message = "Our chain is authoritative"

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
        "message": message,
        "length": len(chain_data),
        "chain": chain_data
    }), 200


if __name__ == "__main__":
    # Run like:  python network_node.py  (then set port via FLASK_RUN_PORT or use flask run)
    app.run(host="0.0.0.0", port=5000, debug=True)
