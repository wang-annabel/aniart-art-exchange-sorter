import { useState } from "react";
import Graph from "./Graph";
import sampleData from "./sampleData";
import StatBox from "./Statbox";

function MatchingCard({ matchingId = 0, data = sampleData }) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="graph-card">
      <div className="graph-card-header">
        <span className="graph-card-title">Matching 1</span>
        <span>
          <button
            className="graph-card-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? "▼" : "▶"}
          </button>
        </span>
      </div>
      {isExpanded && (
        <div className="graph-card-content">
          <div className="graph-card-graph-content">
            <span id="statbox">
              <StatBox participants={30} cycles={5} unmatched={0} />
            </span>
            <span>
              <Graph data={data} />
            </span>
          </div>

          <div className="graph-card-buttons">
            <span>
              <button id="rematch-btn">Rematch</button>
            </span>
            <span>
              <button id="confirm-btn">Confirm</button>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default MatchingCard;
