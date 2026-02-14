"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";
import { required } from "@/lib/validate";
import { canEditRole, roleFromWorkspaces } from "@/lib/roles";
import PermissionHint from "@/components/PermissionHint";

export default function WorkspacesPage() {
  const searchParams = useSearchParams();
  const [workspaces, setWorkspaces] = useState([]);
  const [projects, setProjects] = useState([]);
  const [newWorkspace, setNewWorkspace] = useState("");
  const [newProject, setNewProject] = useState({ workspace_id: "", name: "" });
  const [retentionEdit, setRetentionEdit] = useState({ workspace_id: "", simulation_retention_days: 30 });
  const [retentionAuditFilter, setRetentionAuditFilter] = useState({
    changed_by_user_id: "",
    changed_at_from: "",
    changed_at_to: "",
  });
  const [retentionAudit, setRetentionAudit] = useState([]);
  const [err, setErr] = useState("");
  const workspaceRole = roleFromWorkspaces(workspaces, newProject.workspace_id);
  const canCreateProject = canEditRole(workspaceRole);
  const retentionRole = roleFromWorkspaces(workspaces, retentionEdit.workspace_id);
  const canUpdateRetention = canEditRole(retentionRole);

  async function refresh() {
    setErr("");
    try {
      const ws = await api.listWorkspaces();
      const pj = await api.listProjects();
      setWorkspaces(ws.items || []);
      setProjects(pj.items || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    if (!requireAuthOrRedirect()) return;
    refresh();
  }, []);

  useEffect(() => {
    const workspaceId = searchParams.get("workspace_id");
    if (workspaceId) {
      setNewProject((prev) => ({ ...prev, workspace_id: workspaceId }));
    }
  }, [searchParams]);

  return (
    <div>
      <h1>Workspaces & Projects</h1>
      {err && <p className="error">{err}</p>}

      <div className="card">
        <h3>Create Workspace</h3>
        <div className="row">
          <input value={newWorkspace} onChange={(e) => setNewWorkspace(e.target.value)} placeholder="workspace name" />
          <button onClick={async () => {
            const nameErr = required(newWorkspace, "workspace name");
            if (nameErr) {
              setErr(nameErr);
              return;
            }
            try {
              await api.createWorkspace(newWorkspace);
              setNewWorkspace("");
              refresh();
            } catch (e) {
              setErr(e.message);
            }
          }}>Create</button>
        </div>
      </div>

      <div className="card">
        <h3>Create Project</h3>
        <div className="row">
          <input value={newProject.workspace_id} onChange={(e) => setNewProject({ ...newProject, workspace_id: e.target.value })} placeholder="workspace_id" />
          <input value={newProject.name} onChange={(e) => setNewProject({ ...newProject, name: e.target.value })} placeholder="project name" />
          <button disabled={!canCreateProject && !!newProject.workspace_id} onClick={async () => {
            const workspaceErr = required(newProject.workspace_id, "workspace_id");
            const nameErr = required(newProject.name, "project name");
            if (workspaceErr || nameErr) {
              setErr(workspaceErr || nameErr);
              return;
            }
            if (!canCreateProject) {
              setErr("You need owner/editor role to create project in this workspace");
              return;
            }
            try {
              await api.createProject(newProject.workspace_id, newProject.name);
              setNewProject({ workspace_id: "", name: "" });
              refresh();
            } catch (e) {
              setErr(e.message);
            }
          }}>Create</button>
        </div>
        {!!newProject.workspace_id && (
          <PermissionHint role={workspaceRole} action="edit" />
        )}
      </div>

      <div className="card">
        <h3>Simulation Retention Policy</h3>
        <div className="row">
          <input
            value={retentionEdit.workspace_id}
            onChange={(e) => setRetentionEdit({ ...retentionEdit, workspace_id: e.target.value })}
            placeholder="workspace_id"
          />
          <input
            type="number"
            min={1}
            max={365}
            value={retentionEdit.simulation_retention_days}
            onChange={(e) =>
              setRetentionEdit({
                ...retentionEdit,
                simulation_retention_days: Number(e.target.value || 30)
              })
            }
            placeholder="retention days"
          />
          <button
            disabled={!canUpdateRetention && !!retentionEdit.workspace_id}
            onClick={async () => {
              const workspaceErr = required(retentionEdit.workspace_id, "workspace_id");
              if (workspaceErr) {
                setErr(workspaceErr);
                return;
              }
              const days = Number(retentionEdit.simulation_retention_days || 0);
              if (!Number.isFinite(days) || days < 1 || days > 365) {
                setErr("simulation_retention_days must be 1..365");
                return;
              }
              if (!canUpdateRetention) {
                setErr("You need owner/editor role to update retention policy");
                return;
              }
              try {
                await api.updateWorkspaceRetention(retentionEdit.workspace_id, days);
                const audit = await api.listWorkspaceRetentionAudit(retentionEdit.workspace_id, {
                  limit: 30,
                  changedByUserId: retentionAuditFilter.changed_by_user_id || undefined,
                  changedAtFrom: retentionAuditFilter.changed_at_from || undefined,
                  changedAtTo: retentionAuditFilter.changed_at_to || undefined,
                });
                setRetentionAudit(audit.items || []);
                refresh();
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Update
          </button>
          <button
            className="secondary"
            onClick={async () => {
              const workspaceErr = required(retentionEdit.workspace_id, "workspace_id");
              if (workspaceErr) {
                setErr(workspaceErr);
                return;
              }
              try {
                const audit = await api.listWorkspaceRetentionAudit(retentionEdit.workspace_id, {
                  limit: 50,
                  changedByUserId: retentionAuditFilter.changed_by_user_id || undefined,
                  changedAtFrom: retentionAuditFilter.changed_at_from || undefined,
                  changedAtTo: retentionAuditFilter.changed_at_to || undefined,
                });
                setRetentionAudit(audit.items || []);
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Load Audit
          </button>
        </div>
        {!!retentionEdit.workspace_id && (
          <PermissionHint role={retentionRole} action="edit" />
        )}
        <div className="row">
          <input
            value={retentionAuditFilter.changed_by_user_id}
            onChange={(e) =>
              setRetentionAuditFilter({ ...retentionAuditFilter, changed_by_user_id: e.target.value })
            }
            placeholder="filter changed_by_user_id"
          />
          <input
            value={retentionAuditFilter.changed_at_from}
            onChange={(e) =>
              setRetentionAuditFilter({ ...retentionAuditFilter, changed_at_from: e.target.value })
            }
            placeholder="changed_at_from (ISO)"
          />
          <input
            value={retentionAuditFilter.changed_at_to}
            onChange={(e) =>
              setRetentionAuditFilter({ ...retentionAuditFilter, changed_at_to: e.target.value })
            }
            placeholder="changed_at_to (ISO)"
          />
        </div>
        {retentionAudit.length > 0 && (
          <>
            <h4>Retention Audit</h4>
            <pre>{JSON.stringify(retentionAudit, null, 2)}</pre>
          </>
        )}
      </div>

      <div className="card">
        <h3>Workspace List</h3>
        <pre>{JSON.stringify(workspaces, null, 2)}</pre>
      </div>

      <div className="card">
        <h3>Project List</h3>
        <pre>{JSON.stringify(projects, null, 2)}</pre>
      </div>
    </div>
  );
}
