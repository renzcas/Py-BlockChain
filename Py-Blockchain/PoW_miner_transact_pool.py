import hashlib
import json
import time


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

    def add_transaction(self, sender, recipient, amount):
        tx = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "timestamp": time.time()
        }
        self.unconfirmed_transactions.append(tx)

    def proof_of_work(self, block):
        """
        Simple PoW:
        Find a nonce such that block.hash starts with `difficulty` zeros.
        """
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
        """
        Take all unconfirmed transactions, add a reward tx,
        build a block, run PoW, and append to chain.
        """
        if not self.unconfirmed_transactions:
            print("No transactions to mine.")
            return None

        # Optional: miner reward transaction
        if miner_address is not None:
            reward_tx = {
                "sender": "NETWORK",
                "recipient": miner_address,
                "amount": reward_amount,
                "timestamp": time.time()
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

        return True


if __name__ == "__main__":
    bc = Blockchain(difficulty=4)

    # Add some transactions to the pool
    bc.add_transaction("Alice", "Bob", 10)
    bc.add_transaction("Bob", "Charlie", 5)
    bc.add_transaction("Charlie", "Dave", 2.5)

    # Mine a block, reward goes to "Miner1"
    bc.mine(miner_address="Miner1")

    # Add more transactions
    bc.add_transaction("Alice", "Eve", 3)
    bc.add_transaction("Miner1", "Alice", 0.5)

    # Mine another block
    bc.mine(miner_address="Miner1")

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
S