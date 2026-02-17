import React, { useEffect, useState } from "react";
import "./blockchain.css";

const API = "http://localhost:5000";

export default function BlockchainPanel() {
  const [chain, setChain] = useState([]);
  const [pending, setPending] = useState([]);
  const [address, setAddress] = useState("");
  const [balance, setBalance] = useState(null);
  const [mining, setMining] = useState(false);

  // Fetch chain
  const loadChain = async () => {
    const res = await fetch(`${API}/chain`);
    const data = await res.json();
    setChain(data.chain);
  };

  // Fetch pending txs
  const loadPending = async () => {
    const res = await fetch(`${API}/pending`);
    const data = await res.json();
    setPending(data);
  };

  // Fetch balance
  const loadBalance = async () => {
    if (!address) return;
    const res = await fetch(`${API}/balance/${address}`);
    const data = await res.json();
    setBalance(data.balance);
  };

  // Mine a block
  const mineBlock = async () => {
    setMining(true);
    const res = await fetch(`${API}/mine?miner_address=${address}`);
    await res.json();
    setMining(false);
    loadChain();
    loadPending();
    loadBalance();
  };

  useEffect(() => {
    loadChain();
    loadPending();
    const interval = setInterval(() => {
      loadChain();
      loadPending();
      if (address) loadBalance();
    }, 3000);
    return () => clearInterval(interval);
  }, [address]);

  return (
    <div className="blockchain-panel">
      <h1>Blockchain Cockpit</h1>

      {/* Wallet + Balance */}
      <div className="wallet-section">
        <h2>Wallet</h2>
        <input
          type="text"
          placeholder="Enter your wallet address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
        <button onClick={loadBalance}>Check Balance</button>
        {balance !== null && (
          <p className="balance">Balance: {balance}</p>
        )}
      </div>

      {/* Mining */}
      <div className="mining-section">
        <h2>Mining</h2>
        <button onClick={mineBlock} disabled={!address || mining}>
          {mining ? "Mining..." : "Mine Block"}
        </button>
      </div>

      {/* Pending Transactions */}
      <div className="pending-section">
        <h2>Pending Transactions</h2>
        {pending.length === 0 && <p>No pending transactions</p>}
        {pending.map((tx, i) => (
          <div key={i} className="tx-card">
            <p><strong>From:</strong> {tx.sender_address}</p>
            <p><strong>To:</strong> {tx.recipient_address}</p>
            <p><strong>Amount:</strong> {tx.amount}</p>
          </div>
        ))}
      </div>

      {/* Blockchain */}
      <div className="chain-section">
        <h2>Blockchain</h2>
        {chain.map((block) => (
          <div key={block.index} className="block-card">
            <h3>Block #{block.index}</h3>
            <p><strong>Hash:</strong> {block.hash}</p>
            <p><strong>Prev:</strong> {block.previous_hash}</p>
            <p><strong>Nonce:</strong> {block.nonce}</p>
            <h4>Transactions</h4>
            {block.transactions.map((tx, i) => (
              <div key={i} className="tx-card">
                {typeof tx === "string" ? (
                  <p>{tx}</p>
                ) : (
                  <>
                    <p><strong>From:</strong> {tx.sender_address}</p>
                    <p><strong>To:</strong> {tx.recipient_address}</p>
                    <p><strong>Amount:</strong> {tx.amount}</p>
                  </>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
