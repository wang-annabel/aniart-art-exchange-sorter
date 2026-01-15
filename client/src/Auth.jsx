// Auth.jsx - Make sure this file exists in client/src/

import { useState } from "react";

function Auth({ apiBase, onSetToken }) {
  const [isRegistration, setIsRegistration] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  function toggleIsRegister() {
    setIsRegistration(!isRegistration);
    setError("");
    setName("");
  }

  async function handleAuth(e) {
    e.preventDefault();
    setIsAuthenticating(true);
    setError("");

    try {
      if (isRegistration) {
        // Registration
        const registerResponse = await fetch(`${apiBase}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email,
            password: password,
            name: name || null,
          }),
        });

        if (!registerResponse.ok) {
          const errorData = await registerResponse.json();
          throw new Error(errorData.detail || "Registration failed");
        }

        // After successful registration, automatically log in
        const loginData = new URLSearchParams();
        loginData.append("username", email);
        loginData.append("password", password);

        const loginResponse = await fetch(`${apiBase}/auth/jwt/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: loginData,
        });

        if (!loginResponse.ok) {
          throw new Error("Login after registration failed");
        }

        const data = await loginResponse.json();
        if (data.access_token) {
          onSetToken(data.access_token);
          localStorage.setItem("token", data.access_token);
        }
      } else {
        // Login
        const loginData = new URLSearchParams();
        loginData.append("username", email);
        loginData.append("password", password);

        const response = await fetch(`${apiBase}/auth/jwt/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: loginData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Login failed");
        }

        const data = await response.json();
        if (data.access_token) {
          onSetToken(data.access_token);
          localStorage.setItem("token", data.access_token);
        } else {
          throw new Error("No access token received");
        }
      }
    } catch (err) {
      setError(err.message);
      console.error("Auth error:", err);
    } finally {
      setIsAuthenticating(false);
    }
  }

  return (
    <section className="auth-container">
      <div>
        <h2>{isRegistration ? "Sign up" : "Log In"}</h2>
        <p>{isRegistration ? "Create an account" : "Welcome back"}</p>
      </div>

      {error && <p className="auth-error">{error}</p>}

      <form onSubmit={handleAuth} className="auth-form">
        {isRegistration && (
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name (optional)"
            type="text"
            className="auth-input"
          />
        )}
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="email"
          type="email"
          required
          className="auth-input"
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="password"
          type="password"
          required
          minLength={3}
          className="auth-input"
        />
        <button
          type="submit"
          disabled={isAuthenticating}
          className="auth-submit-btn"
        >
          {isAuthenticating ? "Authenticating..." : "Submit"}
        </button>
      </form>

      <hr className="auth-divider" />

      <div className="auth-toggle">
        <p>
          {isRegistration
            ? "Already have an account?"
            : "Don't have an account?"}
        </p>
        <button
          onClick={toggleIsRegister}
          type="button"
          className="auth-toggle-btn"
        >
          {isRegistration ? "Log in" : "Sign up"}
        </button>
      </div>
    </section>
  );
}

export default Auth;
