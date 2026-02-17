import hashlib
import time
import json

class Block:
    def __init__(self, index, data, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, "Genesis Block", "0")
        self.chain.append(genesis)

    def add_block(self, data):
        prev_block = self.chain[-1]
        new_block = Block(len(self.chain), data, prev_block.hash)
        self.chain.append(new_block)

    def is_valid(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]

            if curr.previous_hash != prev.hash:
                return False

            if curr.hash != curr.compute_hash():
                return False

        return True


# Demo
if __name__ == "__main__":
    bc = Blockchain()
    bc.add_block({"amount": 10, "from": "Alice", "to": "Bob"})
    bc.add_block({"amount": 20, "from": "Bob", "to": "Charlie"})

    for block in bc.chain:
        print(vars(block))

    print("Blockchain valid:", bc.is_valid())
