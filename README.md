# Py-BlockChain

ow to play with the network
1. Run multiple nodes (e.g. different terminals):

Node 1: port 5000

Node 2: port 5001

Node 3: port 5002

2. Register peers on each node:


# On node 1 (port 5000)
curl -X POST -H "Content-Type: application/json" \
  -d '{"nodes": ["http://localhost:5001", "http://localhost:5002"]}' \
  http://localhost:5000/nodes/register

3. Submit transactions and mine on any node.

4. Trigger consensus:

bash
curl http://localhost:5001/nodes/resolve
curl http://localhost:5002/nodes/resolve

They’ll adopt the longest valid chain.


ore Networking Concepts
1. Node Discovery
Nodes register each other via:

Code
POST /nodes/register
Each node stores a set of peers.

2. Peer List
Nodes can list their peers:

Code
GET /nodes
3. Longest‑Chain Rule
Nodes resolve conflicts:

Code
GET /nodes/resolve
Each node:

Fetches chains from peers

Validates them

Replaces its own chain if a longer valid one exists

4. Block Propagation
After mining, a node notifies peers to run consensus.


,,,,,,,,,,,,,,,,,,,,,,,,,,,,

🧩 Full Multi‑Node Networking Code (clean + modular)
Below is the networking layer only, ready to drop into your existing Flask blockchain file.

python
# ---------------------------
# MULTI-NODE NETWORKING LAYER
# ---------------------------

from urllib.parse import urlparse
import requests

class Blockchain:
    def __init__(self, difficulty=3):
        self.unconfirmed_transactions = []
        self.chain = []
        self.nodes = set()
        self.difficulty = difficulty
        self.create_genesis_block()

    # ---------------------------
    # NODE DISCOVERY
    # ---------------------------

    def register_node(self, address):
        """
        Add a new node to the peer list.
        address: 'http://host:port'
        """
        parsed = urlparse(address)
        node_url = f"{parsed.scheme}://{parsed.netloc}"
        self.nodes.add(node_url)

    # ---------------------------
    # CONSENSUS: LONGEST VALID CHAIN
    # ---------------------------

    def resolve_conflicts(self):
        """
        Implements the longest-chain rule.
        Returns True if chain was replaced.
        """
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            try:
                response = requests.get(f"{node}/chain", timeout=2)
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
            self.chain = [
                Block(
                    index=b["index"],
                    transactions=b["transactions"],
                    timestamp=b["timestamp"],
                    previous_hash=b["previous_hash"],
                    nonce=b["nonce"],
                    hash_value=b["hash"]
                )
                for b in new_chain
            ]
            return True

        return False

    # ---------------------------
    # BLOCK PROPAGATION
    # ---------------------------

    def broadcast_new_block(self):
        """
        Notify peers to run consensus after mining.
        """
        for node in self.nodes:
            try:
                requests.get(f"{node}/nodes/resolve", timeout=2)
            except requests.exceptions.RequestException:
                pass
🧩 Networking Endpoints (Flask)
Add these to your Flask app:

python
@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    data = request.get_json()
    nodes = data.get("nodes")

    if nodes is None or not isinstance(nodes, list):
        return jsonify({"message": "Please supply a list of nodes"}), 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({
        "message": "Nodes added",
        "total_nodes": list(blockchain.nodes)
    }), 201


@app.route("/nodes", methods=["GET"])
def list_nodes():
    return jsonify({"nodes": list(blockchain.nodes)}), 200


@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    replaced = blockchain.resolve_conflicts()
    message = "Chain replaced" if replaced else "Chain authoritative"

    chain_data = [
        {
            "index": b.index,
            "timestamp": b.timestamp,
            "previous_hash": b.previous_hash,
            "hash": b.hash,
            "nonce": b.nonce,
            "transactions": b.transactions
        }
        for b in blockchain.chain
    ]

    return jsonify({
        "message": message,
        "length": len(chain_data),
        "chain": chain_data
    }), 200
🧪 How to Run a Multi‑Node Network
Terminal 1
Code
flask run --port 5000
Terminal 2
Code
flask run --port 5001
Terminal 3
Code
flask run --port 5002
🔗 Register Nodes
On node 5000:

bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"nodes": ["http://localhost:5001", "http://localhost:5002"]}' \
  http://localhost:5000/nodes/register
On node 5001:

bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"nodes": ["http://localhost:5000", "http://localhost:5002"]}' \
  http://localhost:5001/nodes/register
⛏️ Mine on any node
bash
curl "http://localhost:5001/mine?miner_address=XYZ"
Nodes 5000 and 5002 will automatically sync via /nodes/resolve.

🌐 Your Network Map Panel (React)
Now that networking is alive, your Network Map panel can show:

Node list

Block height

Chain validity

Peer count

Sync status

If you want, I can now upgrade your Network Map panel to:

Auto‑discover peers

Visualize nodes as a graph

Show block propagation animations

Show consensus events in real time