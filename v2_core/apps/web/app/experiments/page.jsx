"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";
import { required } from "@/lib/validate";
import { canEditRole, roleFromProjects } from "@/lib/roles";
import PermissionHint from "@/components/PermissionHint";

export default function ExperimentsPage() {
  const searchParams = useSearchParams();
  const [projectId, setProjectId] = useState("");
  const [projects, setProjects] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [newExp, setNewExp] = useState({
    hypothesis: "",
    primary_metric: "purchase_conversion",
    guardrail_metrics: "bounce_rate"
  });
  const [experimentId, setExperimentId] = useState("");
  const [variants, setVariants] = useState([]);
  const [newVariant, setNewVariant] = useState({
    variant_key: "test_b",
    traffic_weight: 10,
    config_json_text: '{"label":"Variant B"}'
  });
  const [runId, setRunId] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const projectRole = roleFromProjects(projects, projectId);
  const canEditProject = canEditRole(projectRole);

  useEffect(() => {
    if (!requireAuthOrRedirect()) return;
    api.listProjects().then((res) => setProjects(res.items || [])).catch(() => {});
    refresh();
  }, []);

  useEffect(() => {
    const qProjectId = searchParams.get("project_id");
    const qExperimentId = searchParams.get("experiment_id");
    const qRunId = searchParams.get("run_id");
    if (qProjectId) setProjectId(qProjectId);
    if (qExperimentId) {
      setExperimentId(qExperimentId);
      loadVariants(qExperimentId);
    }
    if (qRunId) setRunId(qRunId);
  }, [searchParams]);

  async function refresh() {
    setErr("");
    try {
      const res = await api.listExperiments(projectId || undefined);
      setExperiments(res.items || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function loadVariants(targetExperimentId = experimentId) {
    setErr("");
    const expErr = required(targetExperimentId, "experiment_id");
    if (expErr) {
      setErr(expErr);
      return;
    }
    try {
      const res = await api.listVariants(targetExperimentId);
      setVariants(res.items || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function analyze() {
    setErr("");
    setMsg("");
    const expErr = required(experimentId, "experiment_id");
    const runErr = required(runId, "run_id");
    if (expErr || runErr) {
      setErr(expErr || runErr);
      return;
    }
    try {
      const res = await api.analyzeExperiment(experimentId, runId);
      setAnalysis(res);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function adopt() {
    setErr("");
    setMsg("");
    const expErr = required(experimentId, "experiment_id");
    const runErr = required(runId, "run_id");
    if (expErr || runErr) {
      setErr(expErr || runErr);
      return;
    }
    try {
      const res = await api.adoptFromAnalysis(experimentId, runId);
      setMsg(`Adopted: ${res.id} / variant=${res.winning_variant_key}`);
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div>
      <h1>Experiments</h1>
      <div className="card">
        <h3>List</h3>
        <div className="row">
          <input placeholder="project_id (optional)" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
          <button onClick={refresh}>Load</button>
        </div>
        <table style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>id</th>
              <th>project</th>
              <th>metric</th>
              <th>status</th>
              <th>action</th>
            </tr>
          </thead>
          <tbody>
            {experiments.map((x) => (
              <tr key={x.id}>
                <td>{x.id}</td>
                <td>{x.project_id}</td>
                <td>{x.primary_metric}</td>
                <td>{x.status}</td>
                <td className="row">
                  <button className="secondary" onClick={() => setExperimentId(x.id)}>Use</button>
                  <button className="secondary" onClick={() => {
                    setExperimentId(x.id);
                    loadVariants(x.id);
                  }}>Use + Variants</button>
                  <button className="secondary" disabled={!canEditRole(x.my_role)} onClick={async () => {
                    try {
                      await api.activateExperiment(x.id);
                      refresh();
                    } catch (e) {
                      setErr(e.message);
                    }
                  }}>Activate</button>
                  <button className="secondary" disabled={!canEditRole(x.my_role)} onClick={async () => {
                    try {
                      await api.deactivateExperiment(x.id);
                      refresh();
                    } catch (e) {
                      setErr(e.message);
                    }
                  }}>Deactivate</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Create</h3>
        <div className="row">
          <input placeholder="project_id" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
          <input
            placeholder="primary_metric"
            value={newExp.primary_metric}
            onChange={(e) => setNewExp({ ...newExp, primary_metric: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <input
            placeholder="hypothesis"
            value={newExp.hypothesis}
            onChange={(e) => setNewExp({ ...newExp, hypothesis: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <input
            placeholder="guardrail metrics csv"
            value={newExp.guardrail_metrics}
            onChange={(e) => setNewExp({ ...newExp, guardrail_metrics: e.target.value })}
          />
          <button disabled={!canEditProject && !!projectId} onClick={async () => {
            setErr("");
            setMsg("");
            const projectErr = required(projectId, "project_id");
            const hypoErr = required(newExp.hypothesis, "hypothesis");
            const metricErr = required(newExp.primary_metric, "primary_metric");
            if (projectErr || hypoErr || metricErr) {
              setErr(projectErr || hypoErr || metricErr);
              return;
            }
            if (!canEditProject) {
              setErr("You need owner/editor role to create experiments in this project");
              return;
            }
            try {
              const created = await api.createExperiment({
                project_id: projectId,
                hypothesis: newExp.hypothesis,
                primary_metric: newExp.primary_metric,
                guardrail_metrics: newExp.guardrail_metrics
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean)
              });
              setMsg(`Created: ${created.id}`);
              setExperimentId(created.id);
              setNewExp({ ...newExp, hypothesis: "" });
              refresh();
            } catch (e) {
              setErr(e.message);
            }
          }}>Create</button>
        </div>
        {!!projectId && <PermissionHint role={projectRole} action="edit" />}
      </div>

      <div className="card">
        <h3>Variants</h3>
        <div className="row">
          <input placeholder="experiment_id" value={experimentId} onChange={(e) => setExperimentId(e.target.value)} />
          <button onClick={() => loadVariants()}>Load Variants</button>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <input
            placeholder="variant_key"
            value={newVariant.variant_key}
            onChange={(e) => setNewVariant({ ...newVariant, variant_key: e.target.value })}
          />
          <input
            type="number"
            min={0}
            max={100}
            step="0.1"
            placeholder="traffic_weight"
            value={newVariant.traffic_weight}
            onChange={(e) => setNewVariant({ ...newVariant, traffic_weight: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <textarea
            rows={2}
            placeholder='config_json, ex: {"label":"Variant B"}'
            value={newVariant.config_json_text}
            onChange={(e) => setNewVariant({ ...newVariant, config_json_text: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <button
            disabled={!canEditProject && !!experimentId}
            onClick={async () => {
              setErr("");
              setMsg("");
              const expErr = required(experimentId, "experiment_id");
              const keyErr = required(newVariant.variant_key, "variant_key");
              if (expErr || keyErr) {
                setErr(expErr || keyErr);
                return;
              }
              try {
                const config = JSON.parse(newVariant.config_json_text || "{}");
                await api.createVariant(experimentId, {
                  variant_key: newVariant.variant_key,
                  traffic_weight: Number(newVariant.traffic_weight),
                  config_json: config
                });
                setMsg("Variant created");
                await loadVariants();
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Add Variant
          </button>
        </div>
        <table style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>key</th>
              <th>weight</th>
              <th>config</th>
              <th>action</th>
            </tr>
          </thead>
          <tbody>
            {variants.map((v) => (
              <tr key={v.id}>
                <td>{v.variant_key}</td>
                <td>{v.traffic_weight}</td>
                <td>{JSON.stringify(v.config_json)}</td>
                <td className="row">
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      const nextWeight = window.prompt("New traffic weight (0~100)", String(v.traffic_weight));
                      if (nextWeight === null) return;
                      try {
                        await api.updateVariant(experimentId, v.variant_key, {
                          traffic_weight: Number(nextWeight)
                        });
                        setMsg("Variant weight updated");
                        await loadVariants();
                      } catch (e) {
                        setErr(e.message);
                      }
                    }}
                  >
                    Weight
                  </button>
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      const nextConfig = window.prompt("New config_json", JSON.stringify(v.config_json || {}));
                      if (nextConfig === null) return;
                      try {
                        await api.updateVariant(experimentId, v.variant_key, {
                          config_json: JSON.parse(nextConfig)
                        });
                        setMsg("Variant config updated");
                        await loadVariants();
                      } catch (e) {
                        setErr(e.message);
                      }
                    }}
                  >
                    Config
                  </button>
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      try {
                        await api.deleteVariant(experimentId, v.variant_key);
                        setMsg("Variant deleted");
                        await loadVariants();
                      } catch (e) {
                        setErr(e.message);
                      }
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Analyze / Adopt</h3>
        <div className="row">
          <input placeholder="experiment_id" value={experimentId} onChange={(e) => setExperimentId(e.target.value)} />
          <input placeholder="run_id" value={runId} onChange={(e) => setRunId(e.target.value)} />
        </div>
        <div className="row" style={{ marginTop: 10 }}>
          <button onClick={analyze}>Analyze</button>
          <button className="secondary" onClick={adopt}>Adopt From Analysis</button>
        </div>
      </div>
      {msg && <p className="ok">{msg}</p>}
      {err && <p className="error">{err}</p>}
      {analysis && (
        <div className="card">
          <pre>{JSON.stringify(analysis, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
