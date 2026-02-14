"use client";

import Link from "next/link";
import { clearToken, getToken } from "@/lib/auth";

export default function NavBar() {
  const adminBypass = process.env.NEXT_PUBLIC_ADMIN_BYPASS === "true";
  const hasToken = typeof window !== "undefined" && !!getToken();

  return (
    <div style={{ background: "#0f172a", color: "#fff" }}>
      <div className="container row" style={{ paddingTop: 12, paddingBottom: 12, justifyContent: "space-between" }}>
        <div className="row">
          <Link href="/">NovaRium V2</Link>
          <Link href="/workspaces">Workspaces</Link>
          <Link href="/sql">SQL Lab</Link>
          <Link href="/experiments">Experiments</Link>
          <Link href="/analytics">Analytics</Link>
          <Link href="/scenarios">Scenarios</Link>
          <Link href="/journey">Journey</Link>
          <Link href="/community">Community</Link>
        </div>
        <div className="row">
          {!adminBypass && !hasToken && <Link href="/login">Login</Link>}
          {!adminBypass && hasToken && (
            <button
              className="secondary"
              onClick={() => {
                clearToken();
                window.location.href = "/login";
              }}
            >
              Logout(Local)
            </button>
          )}
          {adminBypass && <span style={{ opacity: 0.8 }}>Admin Bypass</span>}
        </div>
      </div>
    </div>
  );
}
