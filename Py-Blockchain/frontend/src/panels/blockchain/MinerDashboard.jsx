import React, { useEffect, useState } from "react";
import "./miner.css";

const API = "http://localhost:5000";

export default function MinerDashboard() {
  const [chain, setChain] = useState([]);
  const [difficulty, setDifficulty] = useState(0);
  const [hashrate, setHashrate] = useState(0);
  const [avgBlockTime, setAvgBlockTime] = useState(0);
  const [minerAddress, setMinerAddress] = useState("");
  const [status, setStatus] = useState("");

  const loadChain = async () => {
    const res = await fetch(`${API}/chain`);
    const data = await res.json();
    setChain(data.chain);

    if (data.chain.length > 1) {
      const times = [];
      for (let i = 1; i < data.chain.length; i++) {
        const t = data.chain[i].timestamp - data.chain[i - 1].timestamp;
        times.push(t);
      }
      const avg = times.reduce((a, b) => a + b, 0) / times.length;
      setAvgBlockTime(avg.toFixed(2));
    }

    setDifficulty(data.chain[1]?.hash.match(/^0+/)?.[0]?.length || 0);
  };

  const simulateHashrate = () => {
    const h = Math.floor(Math.random() * 5000000) + 1000000;
    setHashrate(h);
  };

  const mine = async () => {
    if (!minerAddress) {
      setStatus("Enter miner address first");
      return;
    }

    setStatus("Mining...");
    const res = await fetch(`${API}/mine?miner_address=${minerAddress}`);
    const data = await res.json();
    setStatus(data.message);
    loadChain();
  };

  useEffect(() => {
    loadChain();
    const interval = setInterval(() => {
      loadChain();
      simulateHashrate();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="miner-panel">
      <h1>Miner Dashboard</h1>

      <div className="section">
        <h2>Miner Address</h2>
        <input
          type="text"
          placeholder="Your wallet address"
          value={minerAddress}
          onChange={(e) => setMinerAddress(e.target.value)}
        />
        <button onClick={mine}>Mine Block</button>
      </div>

      <div className="section">
        <h2>Network Stats</h2>
        <p><strong>Difficulty:</strong> {difficulty}</p>
        <p><strong>Simulated Hashrate:</strong> {hashrate.toLocaleString()} H/s</p>
        <p><strong>Avg Block Time:</strong> {avgBlockTime} sec</p>
      </div>

      {status && <p className="status">{status}</p>}
    </div>
  );
}
