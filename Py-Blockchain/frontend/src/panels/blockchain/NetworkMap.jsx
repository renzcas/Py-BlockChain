import React, { useEffect, useState } from "react";
import "./network.css";

const API = "http://localhost:5000";

export default function NetworkMap() {
  const [selfInfo, setSelfInfo] = useState(null);

  const loadSelf = async () => {
    const res = await fetch(`${API}/chain`);
    const data = await res.json();
    setSelfInfo({
      height: data.length,
      valid: data.valid,
      url: API
    });
  };

  useEffect(() => {
    loadSelf();
    const interval = setInterval(loadSelf, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="network-panel">
      <h1>Network Map</h1>

      {selfInfo && (
        <div className="node-card">
          <h2>This Node</h2>
          <p><strong>URL:</strong> {selfInfo.url}</p>
          <p><strong>Height:</strong> {selfInfo.height}</p>
          <p><strong>Valid:</strong> {selfInfo.valid ? "Yes" : "No"}</p>
        </div>
      )}

      <p className="note">
        Multi-node consensus coming next — this panel will auto‑discover peers and visualize the network graph.
      </p>
    </div>
  );
}
