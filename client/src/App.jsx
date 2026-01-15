// App.jsx - FIXED with Auth import and component

import { useState, useEffect } from "react";
import Graph from "./Graph";
import Cards from "./Cards";
import MatchingCard from "./MatchingCard";
import Auth from "./Auth"; // <-- THIS WAS MISSING!
import "./App.css";
import UploadBtn from "./UploadBtn";

function App() {
  const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);

  // Load from localStorage on mount with validation
  const [matchings, setMatchings] = useState(() => {
    try {
      const saved = localStorage.getItem("matchings");
      if (!saved) return [];

      const parsed = JSON.parse(saved);
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

  // Verify token on mount and when token changes
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setIsLoggedIn(false);
        setUser(null);
        return;
      }

      try {
        const response = await fetch(`${apiBase}/auth/verify`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
          setIsLoggedIn(true);
        } else {
          // Token is invalid
          console.warn("Token verification failed");
          handleLogout();
        }
      } catch (error) {
        console.error("Error verifying token:", error);
        handleLogout();
      }
    };

    verifyToken();
  }, [token]);

  function handleSetToken(newToken) {
    setToken(newToken);
    setShowAuth(false);
  }

  async function handleLogout() {
    try {
      // Call logout endpoint
      if (token) {
        await fetch(`${apiBase}/auth/jwt/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear all local state and caches
      localStorage.removeItem("token");
      localStorage.removeItem("matchings");
      localStorage.removeItem("matchingCache");
      localStorage.removeItem("fileIds");

      setToken(null);
      setIsLoggedIn(false);
      setUser(null);
      setMatchings([]);
      setMatchingCache({});
      setFileIds({});
    }
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
    if (!matchingId || typeof matchingId !== "string") {
      console.error("Invalid matchingId:", matchingId);
      return;
    }

    try {
      console.log("Fetching matching data for:", matchingId);

      const response = await fetch(`${apiBase}/matchings/${matchingId}`);

      if (!response.ok) {
        if (response.status === 404) {
          console.warn(
            `Matching ${matchingId} not found on server, removing from cache`
          );

          setMatchings((prev) => prev.filter((id) => id !== matchingId));
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

          return;
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
      if (!error.message.includes("404")) {
        alert(`Error fetching matching data: ${error.message}`);
      }
    }
  };

  // Fetch matching data for any matchings that don't have data yet
  useEffect(() => {
    if (matchings.length === 0) return;

    matchings.forEach((matchingId) => {
      if (!matchingCache[matchingId]) {
        fetchMatchingData(matchingId);
      }
    });
  }, [matchings]);

  // Single handler for both upload and rematch
  const handleMatchingCreated = (matchingId, fileId) => {
    console.log("Matching created:", matchingId, "File ID:", fileId);

    if (!matchingId || typeof matchingId !== "string") {
      console.error("Invalid matchingId received:", matchingId);
      return;
    }

    if (!fileId || typeof fileId !== "string") {
      console.error("Invalid fileId received:", fileId);
      return;
    }

    setMatchings((prev) => [...prev, matchingId]);
    setFileIds((prev) => ({ ...prev, [matchingId]: fileId }));

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
          {isLoggedIn ? (
            <div
              style={{ display: "flex", gap: "0.5em", alignItems: "center" }}
            >
              <span>Logged in as {user?.name || user?.email}</span>
              <button onClick={handleLogout}>Logout</button>
            </div>
          ) : (
            <button onClick={() => setShowAuth(!showAuth)}>
              {showAuth ? "Cancel" : "Login / Sign Up"}
            </button>
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

        {/* CRITICAL: Show Auth component when showAuth is true */}
        {showAuth && !isLoggedIn && (
          <div
            style={{ marginTop: "2em", maxWidth: "400px", margin: "2em auto" }}
          >
            <Auth apiBase={apiBase} onSetToken={handleSetToken} />
          </div>
        )}

        {/* Only show upload button when not showing auth */}
        {!showAuth && (
          <UploadBtn
            apiBase={apiBase}
            token={token}
            onUpdateMatchingCache={handleMatchingCreated}
          />
        )}
      </div>

      <div id="content">
        {matchings.length === 0 && !showAuth && <Cards />}

        {matchings.length > 0 && !showAuth && (
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
                  token={token}
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
