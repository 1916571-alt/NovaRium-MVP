"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";
import { required } from "@/lib/validate";

export default function HomePage() {
  const [me, setMe] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [projects, setProjects] = useState([]);
  const [projectCards, setProjectCards] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [onboarding, setOnboarding] = useState({
    template: "commerce",
    seedPreset: "standard",
    workspaceName: "My Workspace",
    projectName: "my-first-platform",
    userCount: 2000,
    seedChallenges: true
  });
  const [bootstrapSummary, setBootstrapSummary] = useState(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function loadDashboard() {
    setErr("");
    const [meRes, pfRes, projectRes] = await Promise.all([
      api.me(),
      api.portfolio(),
      api.listProjects()
    ]);
    setMe(meRes);
    setPortfolio(pfRes);

    const items = (projectRes?.items || []).slice(0, 6);
    setProjects(items);
    if (!items.length) {
      setProjectCards([]);
      return;
    }

    const cards = await Promise.all(
      items.map(async (p) => {
        try {
          const [expRes, funnel, feedRes] = await Promise.all([
            api.listExperiments(p.id),
            api.getFunnelOverview(p.id),
            api.listCommunityPosts(p.id, "recent", 100)
          ]);
          const exps = expRes?.items || [];
          const active = exps.filter((x) => x.status === "active").length;
          const lastStep = funnel?.steps?.[funnel.steps.length - 1];
          const posts = feedRes?.items || [];
          const nowMs = Date.now();
          const weekMs = 7 * 24 * 60 * 60 * 1000;
          const postCount7d = posts.filter((x) => {
            const ts = Date.parse(x.created_at || "");
            if (Number.isNaN(ts)) return false;
            return nowMs - ts <= weekMs;
          }).length;
          const forkCountTotal = posts.reduce((acc, x) => acc + (x.fork_count || 0), 0);
          return {
            id: p.id,
            name: p.name,
            workspace_id: p.workspace_id,
            experiments_total: exps.length,
            experiments_active: active,
            bottleneck_step: funnel?.bottleneck_step || null,
            total_users: funnel?.total_users || 0,
            end_conversion_rate: lastStep?.conversion_rate || 0,
            post_count_7d: postCount7d,
            fork_count_total: forkCountTotal
          };
        } catch {
          return {
            id: p.id,
            name: p.name,
            workspace_id: p.workspace_id,
            experiments_total: 0,
            experiments_active: 0,
            bottleneck_step: null,
            total_users: 0,
            end_conversion_rate: 0,
            post_count_7d: 0,
            fork_count_total: 0
          };
        }
      })
    );
    setProjectCards(cards);
  }

  useEffect(() => {
    if (!requireAuthOrRedirect()) return;
    Promise.all([loadDashboard(), api.listSimulationTemplates()])
      .then(([, templateRes]) => {
        const items = templateRes.items || [];
        setTemplates(items);
        if (items.length) {
          const t = items[0];
          const preset = t.preset_defaults?.standard || {};
          setOnboarding((prev) => ({
            ...prev,
            template: t.key,
            seedPreset: "standard",
            userCount: preset.user_count || t.default_user_count
          }));
        }
      })
      .catch((e) => setErr(e.message));
  }, []);

  const summary = portfolio?.summary;

  return (
    <div>
      <h1>NovaRium V2</h1>
      <p className="muted">SQL + Experiment + Adoption + Journey + Community</p>
      <div className="card">
        <h3>Quick Onboarding</h3>
        <p className="muted">Create workspace, create project, bootstrap synthetic data in one action.</p>
        <div className="row">
          <select
            value={onboarding.template}
            onChange={(e) => {
              const key = e.target.value;
              const found = templates.find((x) => x.key === key);
              const preset = found?.preset_defaults?.[onboarding.seedPreset] || {};
              setOnboarding((prev) => ({
                ...prev,
                template: key,
                userCount: preset.user_count || found?.default_user_count || prev.userCount
              }));
            }}
          >
            {templates.map((t) => (
              <option key={t.key} value={t.key}>
                {t.key}
              </option>
            ))}
          </select>
          <select
            value={onboarding.seedPreset}
            onChange={(e) => {
              const presetKey = e.target.value;
              const found = templates.find((x) => x.key === onboarding.template);
              const preset = found?.preset_defaults?.[presetKey] || {};
              setOnboarding((prev) => ({
                ...prev,
                seedPreset: presetKey,
                userCount: preset.user_count || found?.default_user_count || prev.userCount
              }));
            }}
          >
            <option value="beginner">beginner</option>
            <option value="standard">standard</option>
            <option value="advanced">advanced</option>
          </select>
          <input
            placeholder="workspace name"
            value={onboarding.workspaceName}
            onChange={(e) => setOnboarding({ ...onboarding, workspaceName: e.target.value })}
          />
          <input
            placeholder="project name"
            value={onboarding.projectName}
            onChange={(e) => setOnboarding({ ...onboarding, projectName: e.target.value })}
          />
          <input
            type="number"
            min={200}
            max={20000}
            placeholder="user_count"
            value={onboarding.userCount}
            onChange={(e) => setOnboarding({ ...onboarding, userCount: e.target.value })}
          />
          <label className="row" style={{ alignItems: "center" }}>
            <input
              type="checkbox"
              checked={onboarding.seedChallenges}
              onChange={(e) => setOnboarding({ ...onboarding, seedChallenges: e.target.checked })}
              style={{ width: "auto" }}
            />
            seed starter SQL challenges
          </label>
          <button
            onClick={async () => {
              setErr("");
              setMsg("");
              const wsErr = required(onboarding.workspaceName, "workspace name");
              const projectErr = required(onboarding.projectName, "project name");
              if (wsErr || projectErr) {
                setErr(wsErr || projectErr);
                return;
              }
              try {
                const ws = await api.createWorkspace(onboarding.workspaceName);
                const pj = await api.createProject(ws.id, onboarding.projectName);
                const sim = await api.bootstrapSimulation(pj.id, {
                  user_count: Number(onboarding.userCount),
                  template: onboarding.template,
                  seed_preset: onboarding.seedPreset,
                  seed_sql_challenges: onboarding.seedChallenges
                });
                setBootstrapSummary({
                  workspace_id: ws.id,
                  project_id: pj.id,
                  experiment_id: sim.experiment_id,
                  run_id: sim.run_id,
                  template: sim.template,
                  seed_preset: sim.seed_preset,
                  sql_challenges_seeded: sim.sql_challenges_seeded
                });
                setMsg(
                  `Onboarding completed: project=${pj.id}, experiment=${sim.experiment_id}, run_id=${sim.run_id}, seed_preset=${sim.seed_preset}, sql_challenges_seeded=${sim.sql_challenges_seeded}`
                );
                await loadDashboard();
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Create + Bootstrap
          </button>
        </div>
        {!!templates.length && (
          <p className="muted">
            {(templates.find((x) => x.key === onboarding.template) || {}).description}
          </p>
        )}
      </div>

      {bootstrapSummary && (
        <div className="card">
          <h3>Latest Bootstrap Summary</h3>
          <div className="row">
            <div className="card metric-card" style={{ flex: 1 }}>
              <div className="muted">workspace_id</div>
              <div>{bootstrapSummary.workspace_id}</div>
            </div>
            <div className="card metric-card" style={{ flex: 1 }}>
              <div className="muted">project_id</div>
              <div>{bootstrapSummary.project_id}</div>
            </div>
            <div className="card metric-card" style={{ flex: 1 }}>
              <div className="muted">experiment_id</div>
              <div>{bootstrapSummary.experiment_id}</div>
            </div>
          </div>
          <div className="row">
            <div className="card metric-card" style={{ flex: 1 }}>
              <div className="muted">run_id</div>
              <div>{bootstrapSummary.run_id}</div>
            </div>
            <div className="card metric-card" style={{ flex: 1 }}>
              <div className="muted">template</div>
              <div>{bootstrapSummary.template}</div>
            </div>
            <div className="card metric-card" style={{ flex: 1 }}>
              <div className="muted">seed_preset</div>
              <div>{bootstrapSummary.seed_preset || "standard"}</div>
            </div>
            <div className="card metric-card" style={{ flex: 1 }}>
              <div className="muted">seeded_sql_challenges</div>
              <div>{bootstrapSummary.sql_challenges_seeded}</div>
            </div>
          </div>
          <div className="row">
            <a className="card metric-card" href={`/workspaces?workspace_id=${encodeURIComponent(bootstrapSummary.workspace_id)}`}>Go Workspace</a>
            <a className="card metric-card" href={`/experiments?project_id=${encodeURIComponent(bootstrapSummary.project_id)}&experiment_id=${encodeURIComponent(bootstrapSummary.experiment_id)}&run_id=${encodeURIComponent(bootstrapSummary.run_id)}`}>Go Experiments</a>
            <a className="card metric-card" href={`/sql?project_id=${encodeURIComponent(bootstrapSummary.project_id)}`}>Go SQL Lab</a>
            <a className="card metric-card" href={`/analytics?project_id=${encodeURIComponent(bootstrapSummary.project_id)}&experiment_id=${encodeURIComponent(bootstrapSummary.experiment_id)}&run_id=${encodeURIComponent(bootstrapSummary.run_id)}&template=${encodeURIComponent(bootstrapSummary.template)}&seed_preset=${encodeURIComponent(bootstrapSummary.seed_preset || "standard")}`}>Go Analytics</a>
            <a className="card metric-card" href={`/journey?project_id=${encodeURIComponent(bootstrapSummary.project_id)}`}>Go Journey</a>
            <a className="card metric-card" href={`/community?project_id=${encodeURIComponent(bootstrapSummary.project_id)}&experiment_id=${encodeURIComponent(bootstrapSummary.experiment_id)}`}>Go Community</a>
          </div>
        </div>
      )}
      <div className="card">
        <h3>Dashboard</h3>
        {summary && (
          <div className="grid-cards">
            <div className="card metric-card">
              <div className="muted">Experiments</div>
              <div>{summary.experiments_total}</div>
            </div>
            <div className="card metric-card">
              <div className="muted">Adopted</div>
              <div>{summary.experiments_adopted}</div>
            </div>
            <div className="card metric-card">
              <div className="muted">SQL Accuracy</div>
              <div>{(summary.sql_accuracy * 100).toFixed(1)}%</div>
            </div>
            <div className="card metric-card">
              <div className="muted">Journey Events</div>
              <div>{summary.journey_events_total}</div>
            </div>
          </div>
        )}
        {me && <p className="muted">Signed in as: {me.email || me.user_id} / projects: {projects.length}</p>}
        {!summary && !err && <p className="muted">Loading...</p>}
      </div>

      <div className="card">
        <h3>Project Snapshots</h3>
        {!projectCards.length && <p className="muted">No projects yet. Use Quick Onboarding above.</p>}
        {!!projectCards.length && (
          <div className="grid-cards">
            {projectCards.map((c) => (
              <div key={c.id} className="card metric-card">
                <div style={{ fontWeight: 600 }}>{c.name}</div>
                <div className="muted">project_id: {c.id}</div>
                <div className="muted">workspace_id: {c.workspace_id}</div>
                <div>experiments: {c.experiments_total} (active {c.experiments_active})</div>
                <div>users in funnel: {c.total_users}</div>
                <div>purchase conversion: {(c.end_conversion_rate * 100).toFixed(2)}%</div>
                <div>bottleneck: {c.bottleneck_step || "-"}</div>
                <div>community posts(7d): {c.post_count_7d}</div>
                <div>community forks(total): {c.fork_count_total}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      {msg && <p className="ok">{msg}</p>}
      {err && <p className="error">{err}</p>}
    </div>
  );
}
