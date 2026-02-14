"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";
import { required } from "@/lib/validate";
import { canEditRole, roleFromWorkspaces } from "@/lib/roles";
import PermissionHint from "@/components/PermissionHint";

function summarizeScenarioPayload(payload) {
  if (!payload || typeof payload !== "object") {
    return {
      experiments: 0,
      variants: 0,
      sql_challenges: 0,
      feature_states: 0,
      community_posts: 0
    };
  }

  let root = payload;
  if (
    payload.data &&
    typeof payload.data === "object" &&
    !Array.isArray(payload.data)
  ) {
    root = payload.data;
  }

  const experiments = Array.isArray(root.experiments) ? root.experiments : [];
  const sqlChallenges =
    Array.isArray(root.sql_challenges) ? root.sql_challenges
      : Array.isArray(root.sqlChallenges) ? root.sqlChallenges : [];
  const featureStates =
    Array.isArray(root.feature_states) ? root.feature_states
      : Array.isArray(root.featureStates) ? root.featureStates : [];
  const communityPosts =
    Array.isArray(root.community_posts) ? root.community_posts
      : Array.isArray(root.communityPosts) ? root.communityPosts : [];
  const variants = experiments.reduce((acc, exp) => {
    if (exp && Array.isArray(exp.variants)) return acc + exp.variants.length;
    return acc;
  }, 0);
  return {
    experiments: experiments.length,
    variants,
    sql_challenges: sqlChallenges.length,
    feature_states: featureStates.length,
    community_posts: communityPosts.length
  };
}

export default function ScenariosPage() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState([]);
  const [workspaces, setWorkspaces] = useState([]);
  const [projectId, setProjectId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [projectName, setProjectName] = useState("Imported Scenario Project");
  const [exportSchemaVersion, setExportSchemaVersion] = useState("scenario-pack-v1");
  const [schemaVersion, setSchemaVersion] = useState("scenario-pack-v1");
  const [payloadJson, setPayloadJson] = useState("{}");
  const [exportJson, setExportJson] = useState("");
  const [shareHours, setShareHours] = useState(24);
  const [shareToken, setShareToken] = useState("");
  const [shareResolveToken, setShareResolveToken] = useState("");
  const [result, setResult] = useState(null);
  const [validateResult, setValidateResult] = useState(null);
  const [err, setErr] = useState("");

  const workspaceRole = roleFromWorkspaces(workspaces, workspaceId);
  const canImport = canEditRole(workspaceRole);

  async function refresh() {
    setErr("");
    try {
      const [pj, ws] = await Promise.all([api.listProjects(), api.listWorkspaces()]);
      setProjects(pj.items || []);
      setWorkspaces(ws.items || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    if (!requireAuthOrRedirect()) return;
    refresh();
  }, []);

  useEffect(() => {
    const qProject = searchParams.get("project_id");
    const qWorkspace = searchParams.get("workspace_id");
    if (qProject) setProjectId(qProject);
    if (qWorkspace) setWorkspaceId(qWorkspace);
  }, [searchParams]);

  const projectNameHint = useMemo(() => {
    const found = projects.find((x) => x.id === projectId);
    return found ? found.name : "";
  }, [projects, projectId]);

  const exportSummary = useMemo(() => {
    if (!exportJson) return summarizeScenarioPayload({});
    try {
      const parsed = JSON.parse(exportJson);
      return summarizeScenarioPayload(parsed.payload || {});
    } catch {
      return summarizeScenarioPayload({});
    }
  }, [exportJson]);

  const importSummary = useMemo(() => {
    try {
      return summarizeScenarioPayload(JSON.parse(payloadJson || "{}"));
    } catch {
      return summarizeScenarioPayload({});
    }
  }, [payloadJson]);

  const summaryDelta = useMemo(
    () => ({
      experiments: importSummary.experiments - exportSummary.experiments,
      variants: importSummary.variants - exportSummary.variants,
      sql_challenges: importSummary.sql_challenges - exportSummary.sql_challenges,
      feature_states: importSummary.feature_states - exportSummary.feature_states,
      community_posts: importSummary.community_posts - exportSummary.community_posts
    }),
    [importSummary, exportSummary]
  );

  return (
    <div>
      <h1>Scenario Packs</h1>
      <p>Export a project learning snapshot and import it into another workspace/project.</p>
      {err && <p className="error">{err}</p>}

      <div className="card">
        <h3>Export</h3>
        <div className="row">
          <input
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            placeholder="project_id"
          />
          <select
            value={exportSchemaVersion}
            onChange={(e) => setExportSchemaVersion(e.target.value)}
          >
            <option value="scenario-pack-v1">scenario-pack-v1</option>
            <option value="scenario-pack-v2">scenario-pack-v2</option>
          </select>
          <button
            onClick={async () => {
              const e1 = required(projectId, "project_id");
              if (e1) {
                setErr(e1);
                return;
              }
              setErr("");
              setResult(null);
              setValidateResult(null);
              try {
                const data = await api.exportScenarioPack(projectId, exportSchemaVersion);
                const pretty = JSON.stringify(data, null, 2);
                setExportJson(pretty);
                setPayloadJson(JSON.stringify(data.payload || {}, null, 2));
                setSchemaVersion(data.schema_version || "scenario-pack-v1");
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Export Pack
          </button>
        </div>
        {projectNameHint && <p>Selected project: <strong>{projectNameHint}</strong></p>}
        <div className="row">
          <input
            type="number"
            min={1}
            max={720}
            value={shareHours}
            onChange={(e) => setShareHours(Number(e.target.value || 24))}
            placeholder="expires hours"
          />
          <button
            className="secondary"
            onClick={async () => {
              const e1 = required(projectId, "project_id");
              if (e1) {
                setErr(e1);
                return;
              }
              if (!Number.isFinite(shareHours) || shareHours < 1 || shareHours > 720) {
                setErr("expires_hours must be 1..720");
                return;
              }
              setErr("");
              try {
                const data = await api.createScenarioShare({
                  project_id: projectId,
                  schema_version: exportSchemaVersion,
                  expires_hours: shareHours
                });
                setShareToken(data.share_token || "");
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Create Share Link
          </button>
          <button
            className="secondary"
            onClick={async () => {
              const token = (shareToken || "").trim();
              const e1 = required(token, "share_token");
              if (e1) {
                setErr(e1);
                return;
              }
              setErr("");
              try {
                const data = await api.revokeScenarioShare(token);
                setResult(data);
                setShareToken("");
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Revoke Share Link
          </button>
        </div>
        {shareToken && (
          <textarea
            rows={2}
            value={shareToken}
            onChange={(e) => setShareToken(e.target.value)}
            style={{ width: "100%" }}
          />
        )}
        {exportJson && (
          <textarea
            rows={14}
            value={exportJson}
            onChange={(e) => setExportJson(e.target.value)}
            style={{ width: "100%" }}
          />
        )}
      </div>

      <div className="card">
        <h3>Import</h3>
        <div className="row">
          <input
            value={workspaceId}
            onChange={(e) => setWorkspaceId(e.target.value)}
            placeholder="workspace_id"
          />
          <input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="new project name"
          />
          <select
            value={schemaVersion}
            onChange={(e) => setSchemaVersion(e.target.value)}
          >
            <option value="scenario-pack-v1">scenario-pack-v1</option>
            <option value="scenario-pack-v2">scenario-pack-v2</option>
          </select>
          <button
            disabled={!canImport && !!workspaceId}
            onClick={async () => {
              const e1 = required(workspaceId, "workspace_id");
              const e2 = required(projectName, "project_name");
              if (e1 || e2) {
                setErr(e1 || e2);
                return;
              }
              if (!canImport) {
                setErr("You need owner/editor role in the target workspace");
                return;
              }
              let parsedPayload = {};
              try {
                parsedPayload = JSON.parse(payloadJson || "{}");
              } catch {
                setErr("payload JSON is invalid");
                return;
              }
              setErr("");
              setResult(null);
              setValidateResult(null);
              try {
                const data = await api.importScenarioPack({
                  workspace_id: workspaceId,
                  project_name: projectName,
                  schema_version: schemaVersion,
                  payload: parsedPayload
                });
                setResult(data);
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Import Pack
          </button>
          <button
            className="secondary"
            onClick={async () => {
              let parsedPayload = {};
              try {
                parsedPayload = JSON.parse(payloadJson || "{}");
              } catch {
                setErr("payload JSON is invalid");
                return;
              }
              setErr("");
              setValidateResult(null);
              try {
                const data = await api.validateScenarioPack({
                  workspace_id: workspaceId || "validate-only",
                  project_name: projectName || "validate-only",
                  schema_version: schemaVersion,
                  payload: parsedPayload
                });
                setValidateResult(data);
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Validate Only
          </button>
        </div>
        {!!workspaceId && <PermissionHint role={workspaceRole} action="edit" />}
        <textarea
          rows={14}
          value={payloadJson}
          onChange={(e) => setPayloadJson(e.target.value)}
          style={{ width: "100%" }}
        />
        <h4>Payload Preview</h4>
        <pre>{JSON.stringify(importSummary, null, 2)}</pre>
        <h4>Delta vs Last Export</h4>
        <pre>{JSON.stringify(summaryDelta, null, 2)}</pre>
      </div>

      <div className="card">
        <h3>Resolve Shared Token</h3>
        <div className="row">
          <input
            value={shareResolveToken}
            onChange={(e) => setShareResolveToken(e.target.value)}
            placeholder="share_token"
          />
          <button
            className="secondary"
            onClick={async () => {
              const e1 = required(shareResolveToken, "share_token");
              if (e1) {
                setErr(e1);
                return;
              }
              setErr("");
              try {
                const data = await api.resolveScenarioShare(shareResolveToken.trim());
                setExportJson(JSON.stringify(data, null, 2));
                setPayloadJson(JSON.stringify(data.payload || {}, null, 2));
                setSchemaVersion(data.schema_version || "scenario-pack-v1");
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Resolve
          </button>
          <button
            className="secondary"
            onClick={async () => {
              const e1 = required(shareResolveToken, "share_token");
              if (e1) {
                setErr(e1);
                return;
              }
              setErr("");
              try {
                const data = await api.revokeScenarioShare(shareResolveToken.trim());
                setResult(data);
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Revoke
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <h3>Import Result</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}

      {validateResult && (
        <div className="card">
          <h3>Validate Result</h3>
          <pre>{JSON.stringify(validateResult, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
