// App.jsx
import { useState, useEffect } from "react";
import Graph from "./Graph";
import Cards from "./Cards";
import MatchingCard from "./MatchingCard";
import "./App.css";
import UploadBtn from "./UploadBtn";

function App() {
  const apiBase = "http://localhost:8000"; // Remove trailing slash and /api/
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token"));

  // Array of matching IDs, not Set
  const [matchings, setMatchings] = useState([]);

  // Store matching data keyed by matching_id
  const [matchingCache, setMatchingCache] = useState({});

  // Check if token exists on mount
  useEffect(() => {
    if (token) {
      setIsLoggedIn(true);
    }
  }, [token]);

  function handleLogout() {
    localStorage.removeItem("token");
    setToken(null);
    setIsLoggedIn(false);
  }

  // Fetch matching data when a new matching is added
  useEffect(() => {
    const fetchLatestMatching = async () => {
      if (matchings.length === 0) return;

      const latestMatchingId = matchings[matchings.length - 1];

      // Skip if we already have this data
      if (matchingCache[latestMatchingId]) return;

      try {
        const response = await fetch(
          `${apiBase}/matchings/${latestMatchingId}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch matching data");
        }

        const data = await response.json();

        setMatchingCache((prev) => ({
          ...prev,
          [latestMatchingId]: data,
        }));
      } catch (error) {
        console.error("Error fetching matching:", error);
      }
    };

    fetchLatestMatching();
  }, [matchings, apiBase]);

  return (
    <>
      <div className="content">
        <h1>Art Exchange Sorter</h1>

        {isLoggedIn && (
          <div>
            <span>Logged in</span>
            <button onClick={handleLogout}>Logout</button>
          </div>
        )}

        <UploadBtn apiBase={apiBase} onUpdateMatchingCache={setMatchings} />
      </div>

      <div id="content">
        {matchings.length === 0 && <Cards />}

        {matchings.length > 0 && (
          <div>
            {matchings.map((matchingId, index) => {
              const data = matchingCache[matchingId];

              if (!data) {
                return (
                  <div key={matchingId} className="graph-card">
                    <div className="graph-card-header">
                      <span>Loading matching {index + 1}...</span>
                    </div>
                  </div>
                );
              }

              return (
                <MatchingCard
                  key={matchingId}
                  matchingId={matchingId}
                  matchingNumber={index + 1}
                  data={data}
                  apiBase={apiBase}
                  isLoggedIn={isLoggedIn}
                  onRematch={() => {
                    // Rematch logic - reuse the same file_id
                    // We'll implement this next
                  }}
                />
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}

export default App;
