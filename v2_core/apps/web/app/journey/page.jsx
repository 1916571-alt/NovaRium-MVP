"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";

export default function JourneyPage() {
  const searchParams = useSearchParams();
  const [projectId, setProjectId] = useState("");
  const [journey, setJourney] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    requireAuthOrRedirect();
  }, []);

  useEffect(() => {
    const qProjectId = searchParams.get("project_id");
    if (qProjectId) {
      setProjectId(qProjectId);
      loadJourney(qProjectId);
    }
  }, [searchParams]);

  async function loadJourney(targetProjectId = projectId) {
    setErr("");
    try {
      const [j, p] = await Promise.all([
        api.myJourney(targetProjectId),
        api.portfolio()
      ]);
      setJourney(j);
      setPortfolio(p);
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div>
      <h1>Journey & Portfolio</h1>
      <div className="card">
        <div className="row">
          <input placeholder="project_id" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
          <button onClick={loadJourney}>Load</button>
        </div>
      </div>
      {err && <p className="error">{err}</p>}
      {portfolio && (
        <div className="card">
          <h3>Portfolio</h3>
          <pre>{JSON.stringify(portfolio, null, 2)}</pre>
        </div>
      )}
      {journey && (
        <div className="card">
          <h3>Journey</h3>
          <pre>{JSON.stringify(journey, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
