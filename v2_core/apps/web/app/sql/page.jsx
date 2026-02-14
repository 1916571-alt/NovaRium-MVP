"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";
import { required } from "@/lib/validate";
import { canEditRole, roleFromProjects } from "@/lib/roles";
import PermissionHint from "@/components/PermissionHint";

export default function SqlPage() {
  const searchParams = useSearchParams();
  const [projectId, setProjectId] = useState("");
  const [query, setQuery] = useState("select now() as ts");
  const [data, setData] = useState(null);
  const [challenges, setChallenges] = useState([]);
  const [snippets, setSnippets] = useState([]);
  const [snippetTitle, setSnippetTitle] = useState("");
  const [snippetTagsCsv, setSnippetTagsCsv] = useState("analysis,funnel");
  const [snippetQuery, setSnippetQuery] = useState("");
  const [snippetTagFilter, setSnippetTagFilter] = useState("");
  const [snippetPinnedOnly, setSnippetPinnedOnly] = useState(false);
  const [selectedChallengeId, setSelectedChallengeId] = useState("");
  const [submission, setSubmission] = useState(null);
  const [newChallenge, setNewChallenge] = useState({
    title: "",
    prompt_md: "",
    difficulty: "easy",
    expected_schema_json: '{"columns":["ts"]}',
    expected_metrics_json: '{"min_row_count":1}'
  });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [projects, setProjects] = useState([]);
  const projectRole = roleFromProjects(projects, projectId);
  const canEditProject = canEditRole(projectRole);

  useEffect(() => {
    if (!requireAuthOrRedirect()) return;
    api.listProjects().then((res) => setProjects(res.items || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const qProjectId = searchParams.get("project_id");
    const qChallengeId = searchParams.get("challenge_id");
    if (qProjectId) setProjectId(qProjectId);
    if (qChallengeId) setSelectedChallengeId(qChallengeId);
  }, [searchParams]);

  async function loadChallenges() {
    setErr("");
    const projectErr = required(projectId, "project_id");
    if (projectErr) {
      setErr(projectErr);
      return;
    }
    try {
      const res = await api.listSqlChallenges(projectId || undefined);
      setChallenges(res.items || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function loadSnippets() {
    setErr("");
    const projectErr = required(projectId, "project_id");
    if (projectErr) {
      setErr(projectErr);
      return;
    }
    try {
      const res = await api.listSqlSnippets(
        projectId || undefined,
        snippetQuery || undefined,
        snippetTagFilter || undefined,
        snippetPinnedOnly
      );
      setSnippets(res.items || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div>
      <h1>SQL Lab</h1>
      <div className="card">
        <h3>Challenges</h3>
        <div className="row">
          <input placeholder="project_id" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
          <input placeholder="search q (title/sql)" value={snippetQuery} onChange={(e) => setSnippetQuery(e.target.value)} />
          <input placeholder="filter tag" value={snippetTagFilter} onChange={(e) => setSnippetTagFilter(e.target.value)} />
          <label className="row" style={{ alignItems: "center" }}>
            <input
              type="checkbox"
              checked={snippetPinnedOnly}
              onChange={(e) => setSnippetPinnedOnly(e.target.checked)}
              style={{ width: "auto" }}
            />
            pinned only
          </label>
          <button onClick={loadChallenges}>Load</button>
          <button className="secondary" onClick={loadSnippets}>Load Snippets</button>
        </div>
        <table style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>id</th>
              <th>title</th>
              <th>difficulty</th>
              <th>action</th>
            </tr>
          </thead>
          <tbody>
            {challenges.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.title}</td>
                <td>{c.difficulty}</td>
                <td>
                  <button className="secondary" onClick={() => setSelectedChallengeId(c.id)}>Use for submit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Saved SQL Snippets</h3>
        <div className="row">
          <input
            placeholder="snippet title"
            value={snippetTitle}
            onChange={(e) => setSnippetTitle(e.target.value)}
          />
          <input
            placeholder="tags csv"
            value={snippetTagsCsv}
            onChange={(e) => setSnippetTagsCsv(e.target.value)}
          />
          <button
            onClick={async () => {
              setErr("");
              setMsg("");
              const projectErr = required(projectId, "project_id");
              const titleErr = required(snippetTitle, "snippet title");
              const queryErr = required(query, "query");
              if (projectErr || titleErr || queryErr) {
                setErr(projectErr || titleErr || queryErr);
                return;
              }
              try {
                await api.createSqlSnippet({
                  project_id: projectId,
                  title: snippetTitle,
                  sql_text: query,
                  tags: snippetTagsCsv.split(",").map((x) => x.trim()).filter(Boolean)
                });
                setMsg("Snippet saved");
                setSnippetTitle("");
                await loadSnippets();
              } catch (e) {
                setErr(e.message);
              }
            }}
          disabled={!canEditProject && !!projectId}
          >
            Save Current Query
          </button>
        </div>
        <table style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>title</th>
              <th>tags</th>
              <th>pin</th>
              <th>updated_at</th>
              <th>action</th>
            </tr>
          </thead>
          <tbody>
            {snippets.map((s) => (
              <tr key={s.id}>
                <td>{s.title}</td>
                <td>{(s.tags || []).join(", ")}</td>
                <td>{s.is_pinned ? "pinned" : "-"}</td>
                <td>{s.updated_at}</td>
                <td className="row">
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      try {
                        await api.updateSqlSnippet(s.id, { is_pinned: !s.is_pinned });
                        setMsg(s.is_pinned ? "Snippet unpinned" : "Snippet pinned");
                        await loadSnippets();
                      } catch (e) {
                        setErr(e.message);
                      }
                    }}
                  >
                    {s.is_pinned ? "Unpin" : "Pin"}
                  </button>
                  <button className="secondary" onClick={() => setQuery(s.sql_text)}>Apply</button>
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      const queryErr = required(query, "query");
                      if (queryErr) {
                        setErr(queryErr);
                        return;
                      }
                      try {
                        await api.updateSqlSnippet(s.id, { sql_text: query });
                        setMsg("Snippet updated from editor query");
                        await loadSnippets();
                      } catch (e) {
                        setErr(e.message);
                      }
                    }}
                  >
                    Overwrite From Editor
                  </button>
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      const nextTitle = window.prompt("New snippet title", s.title);
                      if (nextTitle === null) return;
                      if (!String(nextTitle).trim()) {
                        setErr("snippet title is required");
                        return;
                      }
                      try {
                        await api.updateSqlSnippet(s.id, { title: String(nextTitle).trim() });
                        setMsg("Snippet renamed");
                        await loadSnippets();
                      } catch (e) {
                        setErr(e.message);
                      }
                    }}
                  >
                    Rename
                  </button>
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      const nextTags = window.prompt("New tags csv", (s.tags || []).join(","));
                      if (nextTags === null) return;
                      try {
                        await api.updateSqlSnippet(s.id, {
                          tags: String(nextTags).split(",").map((x) => x.trim()).filter(Boolean)
                        });
                        setMsg("Snippet tags updated");
                        await loadSnippets();
                      } catch (e) {
                        setErr(e.message);
                      }
                    }}
                  >
                    Retag
                  </button>
                  <button
                    className="secondary"
                    disabled={!canEditProject}
                    onClick={async () => {
                      setErr("");
                      setMsg("");
                      try {
                        await api.deleteSqlSnippet(s.id);
                        setMsg("Snippet deleted");
                        await loadSnippets();
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
        <h3>Create Challenge</h3>
        <div className="row">
          <input
            placeholder="title"
            value={newChallenge.title}
            onChange={(e) => setNewChallenge({ ...newChallenge, title: e.target.value })}
          />
          <select
            value={newChallenge.difficulty}
            onChange={(e) => setNewChallenge({ ...newChallenge, difficulty: e.target.value })}
          >
            <option value="easy">easy</option>
            <option value="medium">medium</option>
            <option value="hard">hard</option>
          </select>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <textarea
            rows={3}
            placeholder="prompt_md"
            value={newChallenge.prompt_md}
            onChange={(e) => setNewChallenge({ ...newChallenge, prompt_md: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <textarea
            rows={2}
            placeholder='expected_schema JSON, ex: {"columns":["ts"]}'
            value={newChallenge.expected_schema_json}
            onChange={(e) => setNewChallenge({ ...newChallenge, expected_schema_json: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <textarea
            rows={2}
            placeholder='expected_metrics JSON, ex: {"min_row_count":1}'
            value={newChallenge.expected_metrics_json}
            onChange={(e) => setNewChallenge({ ...newChallenge, expected_metrics_json: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <button
            disabled={!canEditProject && !!projectId}
            onClick={async () => {
              setErr("");
              setMsg("");
              const projectErr = required(projectId, "project_id");
              const titleErr = required(newChallenge.title, "title");
              const promptErr = required(newChallenge.prompt_md, "prompt_md");
              if (projectErr || titleErr || promptErr) {
                setErr(projectErr || titleErr || promptErr);
                return;
              }
              try {
                const expectedSchema = JSON.parse(newChallenge.expected_schema_json || "{}");
                const expectedMetrics = JSON.parse(newChallenge.expected_metrics_json || "{}");
                const created = await api.createSqlChallenge({
                  project_id: projectId,
                  title: newChallenge.title,
                  prompt_md: newChallenge.prompt_md,
                  difficulty: newChallenge.difficulty,
                  expected_schema: expectedSchema,
                  expected_metrics: expectedMetrics
                });
                setMsg(`Challenge created: ${created.id}`);
                setSelectedChallengeId(created.id);
                loadChallenges();
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Create Challenge
          </button>
        </div>
        {!!projectId && (
          <PermissionHint role={projectRole} action="edit" />
        )}
      </div>

      <div className="card">
        <textarea
          rows={8}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="SELECT ... only"
        />
        <div className="row" style={{ marginTop: 10 }}>
          <button
            onClick={async () => {
              setErr("");
              setMsg("");
              setData(null);
              try {
                const res = await api.executeSql(query, 100);
                setData(res);
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Execute
          </button>
          <button
            className="secondary"
            onClick={async () => {
              setErr("");
              setMsg("");
              setSubmission(null);
              const challengeErr = required(selectedChallengeId, "challenge_id");
              if (challengeErr) {
                setErr(challengeErr);
                return;
              }
              try {
                const res = await api.submitSqlChallenge(selectedChallengeId, query);
                setSubmission(res);
                setMsg(`Submitted: correct=${String(res.is_correct)}`);
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Submit To Challenge
          </button>
        </div>
        <p className="muted" style={{ marginTop: 8 }}>selected challenge: {selectedChallengeId || "-"}</p>
      </div>
      {msg && <p className="ok">{msg}</p>}
      {err && <p className="error">{err}</p>}
      {data && (
        <div className="card">
          <p className="muted">
            rows={data.row_count} truncated={String(data.truncated)}
          </p>
          <table>
            <thead>
              <tr>
                {data.columns.map((c) => (
                  <th key={c}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row, i) => (
                <tr key={i}>
                  {row.map((v, j) => (
                    <td key={j}>{String(v)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {submission && (
        <div className="card">
          <h3>Submission Result</h3>
          <pre>{JSON.stringify(submission, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
