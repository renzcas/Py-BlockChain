import hashlib
import json
import time
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError


# ---------- Wallet / Keys / Addresses ----------

class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    @property
    def address(self):
        """
        Simple address: RIPEMD160(SHA256(pubkey_bytes))
        """
        pub_bytes = self.public_key.to_string()
        sha = hashlib.sha256(pub_bytes).digest()
        ripe = hashlib.new("ripemd160", sha).hexdigest()
        return ripe

    def sign(self, message: str) -> str:
        """
        Sign an arbitrary message (string) and return hex signature.
        """
        message_bytes = message.encode()
        signature = self.private_key.sign(message_bytes)
        return signature.hex()


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
    def __init__(self, difficulty=4):
        self.unconfirmed_transactions = []  # transaction pool
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

    # ---------- Transactions with signatures ----------

    def create_transaction_message(self, sender, recipient, amount, timestamp):
        """
        Canonical message format for signing.
        """
        tx_core = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "timestamp": timestamp
        }
        return json.dumps(tx_core, sort_keys=True)

    def add_signed_transaction(self, sender_pubkey_hex, recipient_address, amount, signature_hex):
        """
        Verify signature and, if valid, add to pool.
        sender_pubkey_hex: hex of sender's public key
        recipient_address: address string
        """
        timestamp = time.time()
        message = self.create_transaction_message(
            sender=pubkey_to_address(sender_pubkey_hex),
            recipient=recipient_address,
            amount=amount,
            timestamp=timestamp
        )

        # Verify signature
        if not verify_signature(sender_pubkey_hex, message, signature_hex):
            print("Invalid signature. Transaction rejected.")
            return False

        tx = {
            "sender_address": pubkey_to_address(sender_pubkey_hex),
            "sender_pubkey": sender_pubkey_hex,
            "recipient_address": recipient_address,
            "amount": amount,
            "timestamp": timestamp,
            "signature": signature_hex
        }

        self.unconfirmed_transactions.append(tx)
        return True

    # ---------- Proof of Work / Mining ----------

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
            print("No transactions to mine.")
            return None

        # Reward transaction (no signature, from NETWORK)
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
            print(f"Block #{new_block.index} mined with hash: {new_block.hash}")
            return new_block
        else:
            print("Failed to add mined block.")
            return None

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

            # Verify all signed transactions
            for tx in curr.transactions:
                if tx == "Genesis Block":
                    continue
                if tx["sender_address"] == "NETWORK":
                    continue  # reward tx

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


# ---------- Demo ----------

if __name__ == "__main__":
    # Create blockchain
    bc = Blockchain(difficulty=3)

    # Create two wallets
    alice = Wallet()
    bob = Wallet()
    miner = Wallet()

    print("Alice address:", alice.address)
    print("Bob address:", bob.address)
    print("Miner address:", miner.address)

    # Alice sends 10 to Bob
    tx_timestamp = time.time()
    tx_message = bc.create_transaction_message(
        sender=alice.address,
        recipient=bob.address,
        amount=10,
        timestamp=tx_timestamp
    )

    # Sign with Alice's private key
    signature_hex = alice.sign(tx_message)

    # Add signed transaction to pool
    bc.add_signed_transaction(
        sender_pubkey_hex=alice.public_key.to_string().hex(),
        recipient_address=bob.address,
        amount=10,
        signature_hex=signature_hex
    )

    # Mine block, reward to miner
    bc.mine(miner_address=miner.address)

    # Print chain
    for block in bc.chain:
        print("-" * 60)
        print(f"Index: {block.index}")
        print(f"Timestamp: {block.timestamp}")
        print(f"Previous Hash: {block.previous_hash}")
        print(f"Nonce: {block.nonce}")
        print(f"Hash: {block.hash}")
        print("Transactions:")
        for tx in block.transactions:
            print("  ", tx)

    print("\nChain valid:", bc.is_chain_valid())
