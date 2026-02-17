import React, { useState } from "react";
import { ec as EC } from "elliptic";
import sha256 from "crypto-js/sha256";
import ripemd160 from "crypto-js/ripemd160";
import AES from "crypto-js/aes";
import Utf8 from "crypto-js/enc-utf8";
import "./wallet.css";

const ec = new EC("secp256k1");

export default function WalletGenerator() {
  const [wallet, setWallet] = useState(null);
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");

  const generateWallet = () => {
    const key = ec.genKeyPair();
    const privateKey = key.getPrivate("hex");
    const publicKey = key.getPublic("hex");
    const address = ripemd160(sha256(publicKey).toString()).toString();

    setWallet({ privateKey, publicKey, address });
    setStatus("Wallet generated");
  };

  const exportKeystore = () => {
    if (!wallet || !password) {
      setStatus("Enter password first");
      return;
    }

    const encrypted = AES.encrypt(JSON.stringify(wallet), password).toString();

    const blob = new Blob([encrypted], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `keystore_${wallet.address}.json`;
    a.click();

    setStatus("Keystore exported");
  };

  return (
    <div className="wallet-panel">
      <h1>Wallet Generator</h1>

      <button onClick={generateWallet}>Generate Wallet</button>

      {wallet && (
        <div className="wallet-info">
          <p><strong>Address:</strong> {wallet.address}</p>
          <p><strong>Public Key:</strong> {wallet.publicKey}</p>
          <p><strong>Private Key:</strong> {wallet.privateKey}</p>
        </div>
      )}

      <div className="export-section">
        <h2>Export Keystore</h2>
        <input
          type="password"
          placeholder="Encryption password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={exportKeystore}>Export JSON Keystore</button>
      </div>

      {status && <p className="status">{status}</p>}
    </div>
  );
}
