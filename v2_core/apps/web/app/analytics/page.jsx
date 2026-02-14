"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";
import { required } from "@/lib/validate";
import { canEditRole, roleFromProjects } from "@/lib/roles";
import PermissionHint from "@/components/PermissionHint";

export default function AnalyticsPage() {
  const searchParams = useSearchParams();
  const [projectId, setProjectId] = useState("");
  const [experimentId, setExperimentId] = useState("");
  const [runId, setRunId] = useState("");
  const [template, setTemplate] = useState("commerce");
  const [seedPreset, setSeedPreset] = useState("standard");
  const [templates, setTemplates] = useState([]);
  const [seedChallenges, setSeedChallenges] = useState(true);
  const [userCount, setUserCount] = useState(2000);
  const [controlRate, setControlRate] = useState(0.22);
  const [testRate, setTestRate] = useState(0.27);
  const [bootstrapRes, setBootstrapRes] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [projects, setProjects] = useState([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const projectRole = roleFromProjects(projects, projectId);
  const canBootstrap = canEditRole(projectRole);

  useEffect(() => {
    if (!requireAuthOrRedirect()) return;
    Promise.all([api.listProjects(), api.listSimulationTemplates()])
      .then(([projectRes, templateRes]) => {
        setProjects(projectRes.items || []);
        const items = templateRes.items || [];
        setTemplates(items);
        const defaultTemplate = items[0];
        if (defaultTemplate) {
          setTemplate(defaultTemplate.key);
          const preset = defaultTemplate.preset_defaults?.standard || {};
          setUserCount(preset.user_count || defaultTemplate.default_user_count);
          setControlRate(
            preset.control_purchase_rate || defaultTemplate.default_control_purchase_rate
          );
          setTestRate(
            preset.test_purchase_rate || defaultTemplate.default_test_purchase_rate
          );
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const qProjectId = searchParams.get("project_id");
    const qExperimentId = searchParams.get("experiment_id");
    const qRunId = searchParams.get("run_id");
    const qTemplate = searchParams.get("template");
    const qSeedPreset = searchParams.get("seed_preset");
    if (qProjectId) setProjectId(qProjectId);
    if (qExperimentId) setExperimentId(qExperimentId);
    if (qRunId) setRunId(qRunId);
    if (qTemplate) setTemplate(qTemplate);
    if (qSeedPreset) setSeedPreset(qSeedPreset);
  }, [searchParams]);

  async function bootstrap() {
    setErr("");
    setMsg("");
    const projectErr = required(projectId, "project_id");
    if (projectErr) {
      setErr(projectErr);
      return;
    }
    if (!canBootstrap) {
      setErr("You need owner/editor role to bootstrap simulation for this project");
      return;
    }
    try {
      const res = await api.bootstrapSimulation(projectId, {
        experiment_id: experimentId || null,
        run_id: runId || null,
        template,
        seed_preset: seedPreset,
        user_count: Number(userCount),
        control_purchase_rate: Number(controlRate),
        test_purchase_rate: Number(testRate),
        seed_sql_challenges: seedChallenges
      });
      setBootstrapRes(res);
      setRunId(res.run_id);
      setExperimentId(res.experiment_id);
      setMsg("Simulation bootstrap completed");
    } catch (e) {
      setErr(e.message);
    }
  }

  async function loadFunnel() {
    setErr("");
    setMsg("");
    const projectErr = required(projectId, "project_id");
    if (projectErr) {
      setErr(projectErr);
      return;
    }
    try {
      const res = await api.getFunnelOverview(
        projectId,
        runId || undefined,
        experimentId || undefined,
        template || undefined
      );
      setFunnel(res);
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div>
      <h1>Analytics</h1>
      <p className="muted">Synthetic data bootstrap + funnel bottleneck overview</p>

      <div className="card">
        <h3>Simulation Bootstrap</h3>
        <div className="row">
          <input placeholder="project_id" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
          <select
            value={template}
            onChange={(e) => {
              const key = e.target.value;
              setTemplate(key);
              const found = templates.find((x) => x.key === key);
              if (found) {
                const preset = found.preset_defaults?.[seedPreset] || {};
                setUserCount(preset.user_count || found.default_user_count);
                setControlRate(
                  preset.control_purchase_rate || found.default_control_purchase_rate
                );
                setTestRate(
                  preset.test_purchase_rate || found.default_test_purchase_rate
                );
              }
            }}
          >
            {templates.map((t) => (
              <option key={t.key} value={t.key}>
                {t.key}
              </option>
            ))}
          </select>
          <select
            value={seedPreset}
            onChange={(e) => {
              const presetKey = e.target.value;
              setSeedPreset(presetKey);
              const found = templates.find((x) => x.key === template);
              if (found) {
                const preset = found.preset_defaults?.[presetKey] || {};
                setUserCount(preset.user_count || found.default_user_count);
                setControlRate(
                  preset.control_purchase_rate || found.default_control_purchase_rate
                );
                setTestRate(
                  preset.test_purchase_rate || found.default_test_purchase_rate
                );
              }
            }}
          >
            <option value="beginner">beginner</option>
            <option value="standard">standard</option>
            <option value="advanced">advanced</option>
          </select>
          <input placeholder="experiment_id (optional)" value={experimentId} onChange={(e) => setExperimentId(e.target.value)} />
          <input placeholder="run_id (optional)" value={runId} onChange={(e) => setRunId(e.target.value)} />
        </div>
        {!!templates.length && (
          <p className="muted">
            {(templates.find((x) => x.key === template) || {}).description}
          </p>
        )}
        <div className="row" style={{ marginTop: 8 }}>
          <input
            type="number"
            min={200}
            max={20000}
            placeholder="user_count"
            value={userCount}
            onChange={(e) => setUserCount(e.target.value)}
          />
          <input
            type="number"
            step="0.01"
            min={0.01}
            max={0.8}
            placeholder="control_purchase_rate"
            value={controlRate}
            onChange={(e) => setControlRate(e.target.value)}
          />
          <input
            type="number"
            step="0.01"
            min={0.01}
            max={0.9}
            placeholder="test_purchase_rate"
            value={testRate}
            onChange={(e) => setTestRate(e.target.value)}
          />
          <label className="row" style={{ alignItems: "center" }}>
            <input
              type="checkbox"
              checked={seedChallenges}
              onChange={(e) => setSeedChallenges(e.target.checked)}
              style={{ width: "auto" }}
            />
            seed starter SQL challenges
          </label>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <button disabled={!canBootstrap && !!projectId} onClick={bootstrap}>Bootstrap</button>
          <button className="secondary" onClick={loadFunnel}>Load Funnel</button>
        </div>
        {!!projectId && (
          <PermissionHint role={projectRole} action="edit" />
        )}
      </div>

      {msg && <p className="ok">{msg}</p>}
      {err && <p className="error">{err}</p>}

      {bootstrapRes && (
        <div className="card">
          <h3>Bootstrap Result</h3>
          <pre>{JSON.stringify(bootstrapRes, null, 2)}</pre>
        </div>
      )}

      {funnel && (
        <div className="card">
          <h3>Funnel Overview</h3>
          <p className="muted">template: {funnel.template}</p>
          <p className="muted">bottleneck: {funnel.bottleneck_step || "-"}</p>
          <table>
            <thead>
              <tr>
                <th>step</th>
                <th>users</th>
                <th>conversion</th>
                <th>dropoff</th>
              </tr>
            </thead>
            <tbody>
              {(funnel.steps || []).map((s) => (
                <tr key={s.step_index}>
                  <td>{s.step_name}</td>
                  <td>{s.users_count}</td>
                  <td>{(s.conversion_rate * 100).toFixed(2)}%</td>
                  <td>{(s.dropoff_rate * 100).toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
