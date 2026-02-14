"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { setRefreshToken, setToken } from "@/lib/auth";
import { required } from "@/lib/validate";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function signIn() {
    setErr("");
    setMsg("");
    const emailErr = required(email, "email");
    const pwdErr = required(password, "password");
    if (emailErr || pwdErr) {
      setErr(emailErr || pwdErr);
      return;
    }
    try {
      const res = await api.signIn(email, password);
      if (res.access_token) setToken(res.access_token);
      if (res.refresh_token) setRefreshToken(res.refresh_token);
      setMsg("Sign in success. Redirecting...");
      setTimeout(() => (window.location.href = "/"), 500);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function signUp() {
    setErr("");
    setMsg("");
    const emailErr = required(email, "email");
    const pwdErr = required(password, "password");
    if (emailErr || pwdErr) {
      setErr(emailErr || pwdErr);
      return;
    }
    try {
      const res = await api.signUp(email, password);
      if (res.access_token) setToken(res.access_token);
      if (res.refresh_token) setRefreshToken(res.refresh_token);
      setMsg("Sign up success. You can sign in now.");
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div>
      <h1>Login</h1>
      <div className="card">
        <div className="row">
          <input placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <div className="row" style={{ marginTop: 10 }}>
          <button onClick={signIn}>Sign In</button>
          <button className="secondary" onClick={signUp}>Sign Up</button>
        </div>
        {msg && <p className="ok">{msg}</p>}
        {err && <p className="error">{err}</p>}
      </div>
    </div>
  );
}
