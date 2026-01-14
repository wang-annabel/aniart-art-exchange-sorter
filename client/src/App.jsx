// App.jsx

import { useState, useEffect } from "react";
import Graph from "./Graph";
import Cards from "./Cards";
import MatchingCard from "./MatchingCard";
import "./App.css";
import UploadBtn from "./UploadBtn";

function App() {
  const apiBase = "http://localhost:8000";
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token"));

  // Load from localStorage on mount with validation
  const [matchings, setMatchings] = useState(() => {
    try {
      const saved = localStorage.getItem("matchings");
      if (!saved) return [];

      const parsed = JSON.parse(saved);
      // Validate that it's an array of strings
      if (
        Array.isArray(parsed) &&
        parsed.every((id) => typeof id === "string")
      ) {
        return parsed;
      }
      console.warn("Invalid matchings in localStorage, clearing");
      localStorage.removeItem("matchings");
      return [];
    } catch (error) {
      console.error("Error loading matchings from localStorage:", error);
      localStorage.removeItem("matchings");
      return [];
    }
  });

  const [matchingCache, setMatchingCache] = useState(() => {
    try {
      const saved = localStorage.getItem("matchingCache");
      return saved ? JSON.parse(saved) : {};
    } catch (error) {
      console.error("Error loading matchingCache from localStorage:", error);
      localStorage.removeItem("matchingCache");
      return {};
    }
  });

  const [fileIds, setFileIds] = useState(() => {
    try {
      const saved = localStorage.getItem("fileIds");
      return saved ? JSON.parse(saved) : {};
    } catch (error) {
      console.error("Error loading fileIds from localStorage:", error);
      localStorage.removeItem("fileIds");
      return {};
    }
  });

  // Save to localStorage whenever state changes
  useEffect(() => {
    try {
      localStorage.setItem("matchings", JSON.stringify(matchings));
    } catch (error) {
      console.error("Error saving matchings to localStorage:", error);
    }
  }, [matchings]);

  useEffect(() => {
    try {
      localStorage.setItem("matchingCache", JSON.stringify(matchingCache));
    } catch (error) {
      console.error("Error saving matchingCache to localStorage:", error);
    }
  }, [matchingCache]);

  useEffect(() => {
    try {
      localStorage.setItem("fileIds", JSON.stringify(fileIds));
    } catch (error) {
      console.error("Error saving fileIds to localStorage:", error);
    }
  }, [fileIds]);

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

  function handleClearSession() {
    if (
      window.confirm(
        "Are you sure you want to clear all matchings? This cannot be undone."
      )
    ) {
      setMatchings([]);
      setMatchingCache({});
      setFileIds({});
      localStorage.removeItem("matchings");
      localStorage.removeItem("matchingCache");
      localStorage.removeItem("fileIds");
    }
  }

  // Helper function to fetch a single matching
  const fetchMatchingData = async (matchingId) => {
    // Validate matchingId
    if (!matchingId || typeof matchingId !== "string") {
      console.error("Invalid matchingId:", matchingId);
      return;
    }

    try {
      console.log("Fetching matching data for:", matchingId);

      const response = await fetch(`${apiBase}/matchings/${matchingId}`);

      if (!response.ok) {
        if (response.status === 404) {
          // Matching doesn't exist on backend - remove it from local state
          console.warn(
            `Matching ${matchingId} not found on server, removing from cache`
          );

          // Remove from all state
          setMatchings((prev) => {
            const updated = prev.filter((id) => id !== matchingId);
            console.log("Updated matchings:", updated);
            return updated;
          });

          setMatchingCache((prev) => {
            const updated = { ...prev };
            delete updated[matchingId];
            return updated;
          });

          setFileIds((prev) => {
            const updated = { ...prev };
            delete updated[matchingId];
            return updated;
          });

          return; // Don't throw error, just silently remove
        }
        throw new Error(`Failed to fetch matching data: ${response.status}`);
      }

      const data = await response.json();

      setMatchingCache((prev) => ({
        ...prev,
        [matchingId]: data,
      }));

      console.log("Matching data fetched successfully:", matchingId);
    } catch (error) {
      console.error("Error fetching matching:", error);
      // Don't show alert for 404s
      if (!error.message.includes("404")) {
        alert(`Error fetching matching data: ${error.message}`);
      }
    }
  };

  // Fetch matching data for any matchings that don't have data yet
  useEffect(() => {
    if (matchings.length === 0) return;

    console.log("Checking matchings for missing data:", matchings);

    matchings.forEach((matchingId) => {
      if (!matchingCache[matchingId]) {
        console.log(`Missing data for ${matchingId}, fetching...`);
        fetchMatchingData(matchingId);
      }
    });
  }, [matchings]);

  // Single handler for both upload and rematch
  const handleMatchingCreated = (matchingId, fileId) => {
    console.log("Matching created:", matchingId, "File ID:", fileId);

    // Validate inputs
    if (!matchingId || typeof matchingId !== "string") {
      console.log(typeof matchingId);
      console.error("Invalid matchingId received:", matchingId);
      return;
    }

    if (!fileId || typeof fileId !== "string") {
      console.error("Invalid fileId received:", fileId);
      return;
    }

    setMatchings((prev) => [...prev, matchingId]);
    setFileIds((prev) => ({ ...prev, [matchingId]: fileId }));

    // Immediately fetch the matching data
    fetchMatchingData(matchingId);
  };

  return (
    <>
      <div className="content">
        <h1>Art Exchange Sorter</h1>

        <div
          style={{
            display: "flex",
            gap: "1em",
            justifyContent: "center",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          {isLoggedIn && (
            <div>
              <span>Logged in</span>
              <button onClick={handleLogout}>Logout</button>
            </div>
          )}

          {matchings.length > 0 && (
            <button
              onClick={handleClearSession}
              style={{ background: "#ef4444", color: "white" }}
            >
              Clear Session
            </button>
          )}
        </div>

        <UploadBtn
          apiBase={apiBase}
          onUpdateMatchingCache={handleMatchingCreated}
        />
      </div>

      <div id="content">
        {matchings.length === 0 && <Cards />}

        {matchings.length > 0 && (
          <div>
            {matchings.map((matchingId, index) => {
              const data = matchingCache[matchingId];
              const fileId = fileIds[matchingId];

              if (!data) {
                return (
                  <div key={matchingId} className="graph-card">
                    <div className="graph-card-header">
                      <span className="graph-card-title">
                        Loading matching {index + 1}...
                      </span>
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
                  fileId={fileId}
                  onRematchComplete={handleMatchingCreated}
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
