import React, { useState } from "react";
import "./transaction.css";
import { ec as EC } from "elliptic";
import sha256 from "crypto-js/sha256";
import ripemd160 from "crypto-js/ripemd160";

const API = "http://localhost:5000";
const ec = new EC("secp256k1");

export default function TransactionComposer() {
  const [privateKey, setPrivateKey] = useState("");
  const [publicKey, setPublicKey] = useState("");
  const [address, setAddress] = useState("");
  const [recipient, setRecipient] = useState("");
  const [amount, setAmount] = useState("");
  const [status, setStatus] = useState("");

  const deriveKeys = () => {
    try {
      const key = ec.keyFromPrivate(privateKey);
      const pub = key.getPublic("hex");
      setPublicKey(pub);

      const addr = ripemd160(sha256(pub).toString()).toString();
      setAddress(addr);

      setStatus("Keys derived successfully");
    } catch (err) {
      setStatus("Invalid private key");
    }
  };

  const sendTransaction = async () => {
    if (!publicKey || !address) {
      setStatus("Derive keys first");
      return;
    }

    const timestamp = Date.now() / 1000;

    const message = JSON.stringify(
      {
        sender: address,
        recipient,
        amount: Number(amount),
        timestamp,
      },
      null,
      0
    );

    const key = ec.keyFromPrivate(privateKey);
    const signature = key.sign(message).toDER("hex");

    const payload = {
      sender_pubkey: publicKey,
      recipient_address: recipient,
      amount: Number(amount),
      signature,
      timestamp,
    };

    const res = await fetch(`${API}/transaction/new`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    setStatus(data.message);
  };

  return (
    <div className="tx-panel">
      <h1>Transaction Composer</h1>

      <div className="section">
        <h2>1. Enter Private Key</h2>
        <input
          type="text"
          placeholder="Private key (hex)"
          value={privateKey}
          onChange={(e) => setPrivateKey(e.target.value)}
        />
        <button onClick={deriveKeys}>Derive Keys</button>
      </div>

      {publicKey && (
        <div className="section">
          <h2>Your Wallet</h2>
          <p><strong>Public Key:</strong> {publicKey}</p>
          <p><strong>Address:</strong> {address}</p>
        </div>
      )}

      <div className="section">
        <h2>2. Create Transaction</h2>
        <input
          type="text"
          placeholder="Recipient address"
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
        />
        <input
          type="number"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <button onClick={sendTransaction}>Send Transaction</button>
      </div>

      {status && <p className="status">{status}</p>}
    </div>
  );
}
