import React, { useState } from "react";
import BlockchainPanel from "./BlockchainPanel";
import TransactionComposer from "./TransactionComposer";
import MinerDashboard from "./MinerDashboard";
import WalletGenerator from "./WalletGenerator";
import NetworkMap from "./NetworkMap";
import "./cockpit.css";

export default function BlockchainCockpit() {
  const [tab, setTab] = useState("explorer");

  const tabs = [
    { id: "explorer", label: "Explorer" },
    { id: "composer", label: "Transaction Composer" },
    { id: "miner", label: "Miner Dashboard" },
    { id: "wallet", label: "Wallet Generator" },
    { id: "network", label: "Network Map" }
  ];

  return (
    <div className="cockpit">
      <h1>Blockchain Cockpit</h1>

      <div className="tab-bar">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={tab === t.id ? "active" : ""}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="panel-container">
        {tab === "explorer" && <BlockchainPanel />}
        {tab === "composer" && <TransactionComposer />}
        {tab === "miner" && <MinerDashboard />}
        {tab === "wallet" && <WalletGenerator />}
        {tab === "network" && <NetworkMap />}
      </div>
    </div>
  );
}
