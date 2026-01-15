// MatchingCard.jsx

import { useState } from "react";
import Graph from "./Graph";
import StatBox from "./Statbox";
import RematchBtn from "./RematchBtn";

function MatchingCard({
  matchingId,
  matchingNumber,
  data,
  apiBase,
  isLoggedIn,
  token,
  fileId,
  onRematchComplete,
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isConfirming, setIsConfirming] = useState(false);

  const handleConfirm = async () => {
    if (!isLoggedIn || !token) {
      alert("Please log in to confirm matchings");
      return;
    }

    try {
      setIsConfirming(true);

      const response = await fetch(
        `${apiBase}/matchings/${matchingId}/confirm`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to confirm matching");
      }

      const result = await response.json();
      alert("Matching confirmed successfully!");
      console.log("Confirmation result:", result);
    } catch (error) {
      console.error("Confirm error:", error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsConfirming(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(
        `${apiBase}/matchings/${matchingId}/download`
      );

      if (!response.ok) {
        throw new Error("Failed to download matching");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `matching_${matchingId}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Download error:", error);
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <div className="graph-card">
      <div className="graph-card-header">
        <span className="graph-card-title">Matching {matchingNumber}</span>

        <button
          className="graph-card-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? "▼" : "▶"}
        </button>
      </div>

      {isExpanded && (
        <div className="graph-card-content">
          <div className="graph-card-graph-content">
            <span id="statbox">
              <StatBox
                participants={data.participants}
                cycles={data.cycles}
                unmatched={data.unmatched}
              />
            </span>
            <span>
              <Graph data={data} />
            </span>
          </div>

          <div className="graph-card-buttons">
            <button id="download-btn" onClick={handleDownload}>
              Download CSV
            </button>

            <RematchBtn
              apiBase={apiBase}
              fileId={fileId}
              onRematchComplete={onRematchComplete}
            />

            <button
              id="confirm-btn"
              onClick={handleConfirm}
              disabled={isConfirming || !isLoggedIn}
              title={!isLoggedIn ? "Login required to confirm" : ""}
            >
              {isConfirming ? "Confirming..." : "Confirm"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default MatchingCard;
