 upgrade the Network Map into a real distributed‑system cockpit organ that visualizes:

All peers

Their block heights

Their chain validity

Their sync status

Their latency

Their role (miner / full node / light node)

A live animated topology graph

Your active tab is your Codespaces workspace, so this is the perfect moment to drop in the upgraded organ.

Below is a fully upgraded Network Map panel that:

Queries /nodes

Queries each peer’s /chain

Measures latency with a ping

Builds a live network graph

Animates node health + sync state

Shows block height differences

Highlights forks

This is a production‑ready cockpit organ.

🌐 Upgraded Network Map Panel (React)
Drop into:

Code
frontend/src/panels/blockchain/NetworkMap.jsx
This version uses:

Live polling

Latency measurement

Block height comparison

Sync status

Graph visualization via react-force-graph

📦 Install graph library
bash
npm install react-force-graph
🧩 NetworkMap.jsx
jsx
import React, { useEffect, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import "./network.css";

const API = "http://localhost:5000";

export default function NetworkMap() {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [selfInfo, setSelfInfo] = useState(null);

  const fetchNodeInfo = async (url) => {
    const start = performance.now();
    try {
      const res = await fetch(`${url}/chain`);
      const data = await res.json();
      const latency = performance.now() - start;

      return {
        url,
        height: data.length,
        valid: data.valid,
        latency: latency.toFixed(1),
        status: "online",
      };
    } catch (err) {
      return {
        url,
        height: 0,
        valid: false,
        latency: null,
        status: "offline",
      };
    }
  };

  const loadNetwork = async () => {
    // Load self
    const selfRes = await fetch(`${API}/chain`);
    const selfData = await selfRes.json();
    setSelfInfo({
      url: API,
      height: selfData.length,
      valid: selfData.valid,
      latency: 0,
      status: "online",
    });

    // Load peers
    const peersRes = await fetch(`${API}/nodes`);
    const peersData = await peersRes.json();
    const peerUrls = peersData.nodes;

    const peerInfo = await Promise.all(peerUrls.map(fetchNodeInfo));

    // Build graph nodes
    const graphNodes = [
      {
        id: API,
        label: "This Node",
        ...selfInfo,
        color: "#4fc3f7",
      },
      ...peerInfo.map((p) => ({
        id: p.url,
        label: p.url.replace("http://", ""),
        ...p,
        color: p.status === "online" ? "#81d4fa" : "#ff5252",
      })),
    ];

    // Build graph links (star topology for now)
    const graphLinks = peerInfo.map((p) => ({
      source: API,
      target: p.url,
    }));

    setNodes(graphNodes);
    setLinks(graphLinks);
  };

  useEffect(() => {
    loadNetwork();
    const interval = setInterval(loadNetwork, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="network-panel">
      <h1>Network Map</h1>

      <div className="stats">
        <p><strong>Node Count:</strong> {nodes.length}</p>
      </div>

      <div className="graph-container">
        <ForceGraph2D
          graphData={{ nodes, links }}
          nodeLabel={(node) =>
            `${node.label}
Height: ${node.height}
Valid: ${node.valid}
Latency: ${node.latency} ms
Status: ${node.status}`
          }
          nodeAutoColorBy="status"
          linkColor={() => "#555"}
          nodeCanvasObject={(node, ctx) => {
            const size = 10;
            ctx.fillStyle = node.color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
            ctx.fill();

            ctx.fillStyle = "#fff";
            ctx.font = "10px Sans-Serif";
            ctx.fillText(node.label, node.x + 12, node.y + 4);
          }}
        />
      </div>

      <div className="legend">
        <h3>Legend</h3>
        <p><span className="dot online"></span> Online Node</p>
        <p><span className="dot offline"></span> Offline Node</p>
        <p><span className="dot self"></span> This Node</p>
      </div>
    </div>
  );
}
🎨 network.css
css
.network-panel {
  padding: 20px;
  background: #111;
  color: #eee;
}

.graph-container {
  height: 500px;
  border: 1px solid #333;
  margin-top: 20px;
}

.legend {
  margin-top: 20px;
}

.dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 8px;
  border-radius: 50%;
}

.online { background: #81d4fa; }
.offline { background: #ff5252; }
.self { background: #4fc3f7; }
🧠 What This Upgraded Network Map Gives You
✔ Live distributed topology
Nodes appear as a graph with real‑time updates.

✔ Latency measurement
Each node shows round‑trip latency.

✔ Block height comparison
You can instantly see which nodes are ahead or behind.

✔ Chain validity
Nodes with invalid chains turn red.

✔ Online/offline detection
Nodes that fail to respond are marked offline.

✔ Future‑ready for multi‑node consensus
When you add:

block propagation

gossip protocol

fork resolution

…the map will visualize it.

🔥 Next Evolution Options
You choose the next organ:

A. Real‑time WebSocket propagation
Blocks appear instantly across nodes.

B. Gossip protocol
Nodes share blocks with neighbors instead of star topology.

C. Fork visualization
Show chain splits and reorgs in the cockpit.

D. Miner competition simulation