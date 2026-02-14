"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { requireAuthOrRedirect } from "@/lib/guard";
import { canEditRole, roleFromProjects } from "@/lib/roles";
import PermissionHint from "@/components/PermissionHint";

export default function CommunityPage() {
  const searchParams = useSearchParams();
  const [sortBy, setSortBy] = useState("recent");
  const [projectId, setProjectId] = useState("");
  const [posts, setPosts] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [newPost, setNewPost] = useState({
    project_id: "",
    experiment_id: "",
    title: "",
    body_md: "",
    tags: "abtest,sql"
  });
  const [newComment, setNewComment] = useState("");
  const [forkPayload, setForkPayload] = useState({
    source_experiment_id: "",
    target_project_id: ""
  });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [projects, setProjects] = useState([]);
  const postRole = roleFromProjects(projects, newPost.project_id);
  const forkTargetRole = roleFromProjects(projects, forkPayload.target_project_id);
  const canCreatePost = !!postRole;
  const canForkToTarget = canEditRole(forkTargetRole);

  async function refreshPosts() {
    setErr("");
    try {
      const res = await api.listCommunityPosts(projectId || undefined, sortBy, 50);
      setPosts(res.items || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function loadComments(postId) {
    setErr("");
    try {
      const res = await api.listCommunityComments(postId);
      setComments(res.items || []);
      setSelectedPost(postId);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    if (!requireAuthOrRedirect()) return;
    api.listProjects().then((res) => setProjects(res.items || [])).catch(() => {});
    refreshPosts();
  }, []);

  useEffect(() => {
    const qProjectId = searchParams.get("project_id");
    const qExperimentId = searchParams.get("experiment_id");
    if (qProjectId) {
      setProjectId(qProjectId);
      setNewPost((prev) => ({ ...prev, project_id: qProjectId }));
      setForkPayload((prev) => ({ ...prev, target_project_id: qProjectId }));
    }
    if (qExperimentId) {
      setNewPost((prev) => ({ ...prev, experiment_id: qExperimentId }));
      setForkPayload((prev) => ({ ...prev, source_experiment_id: qExperimentId }));
    }
  }, [searchParams]);

  useEffect(() => {
    refreshPosts();
  }, [sortBy]);

  return (
    <div>
      <h1>Community</h1>

      <div className="card">
        <h3>Feed</h3>
        <div className="row">
          <input
            placeholder="project_id (optional)"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          />
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="recent">recent</option>
            <option value="ranked">ranked</option>
          </select>
          <button onClick={refreshPosts}>Reload</button>
        </div>
        <table style={{ marginTop: 10 }}>
          <thead>
            <tr>
              <th>title</th>
              <th>project</th>
              <th>exp</th>
              <th>comments</th>
              <th>forks</th>
              <th>score</th>
              <th>action</th>
            </tr>
          </thead>
          <tbody>
            {posts.map((p) => (
              <tr key={p.id}>
                <td>{p.title}</td>
                <td>{p.project_id}</td>
                <td>{p.experiment_id || "-"}</td>
                <td>{p.comment_count}</td>
                <td>{p.fork_count}</td>
                <td>{(p.rank_score || 0).toFixed(3)}</td>
                <td>
                  <button className="secondary" onClick={() => loadComments(p.id)}>
                    comments
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Create Post</h3>
        <div className="row">
          <input
            placeholder="project_id"
            value={newPost.project_id}
            onChange={(e) => setNewPost({ ...newPost, project_id: e.target.value })}
          />
          <input
            placeholder="experiment_id (optional)"
            value={newPost.experiment_id}
            onChange={(e) => setNewPost({ ...newPost, experiment_id: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <input
            placeholder="title"
            value={newPost.title}
            onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <textarea
            rows={4}
            placeholder="body_md"
            value={newPost.body_md}
            onChange={(e) => setNewPost({ ...newPost, body_md: e.target.value })}
          />
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <input
            placeholder="tags csv"
            value={newPost.tags}
            onChange={(e) => setNewPost({ ...newPost, tags: e.target.value })}
          />
          <button
            disabled={!canCreatePost}
            onClick={async () => {
              setErr("");
              setMsg("");
              try {
                await api.createCommunityPost({
                  project_id: newPost.project_id,
                  experiment_id: newPost.experiment_id || null,
                  title: newPost.title,
                  body_md: newPost.body_md,
                  tags: newPost.tags
                    .split(",")
                    .map((x) => x.trim())
                    .filter(Boolean)
                });
                setMsg("Post created");
                refreshPosts();
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Create Post
          </button>
        </div>
        {!!newPost.project_id && <PermissionHint role={postRole} action="view" />}
      </div>

      <div className="card">
        <h3>Comments {selectedPost ? `for ${selectedPost}` : ""}</h3>
        {selectedPost && (
          <>
            <div className="row">
              <input
                placeholder="new comment"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
              />
              <button
                onClick={async () => {
                  setErr("");
                  setMsg("");
                  try {
                    await api.createCommunityComment(selectedPost, newComment);
                    setNewComment("");
                    setMsg("Comment added");
                    loadComments(selectedPost);
                  } catch (e) {
                    setErr(e.message);
                  }
                }}
              >
                Add Comment
              </button>
            </div>
            <pre style={{ marginTop: 8 }}>{JSON.stringify(comments, null, 2)}</pre>
          </>
        )}
      </div>

      <div className="card">
        <h3>Fork Experiment</h3>
        <div className="row">
          <input
            placeholder="source_experiment_id"
            value={forkPayload.source_experiment_id}
            onChange={(e) => setForkPayload({ ...forkPayload, source_experiment_id: e.target.value })}
          />
          <input
            placeholder="target_project_id"
            value={forkPayload.target_project_id}
            onChange={(e) => setForkPayload({ ...forkPayload, target_project_id: e.target.value })}
          />
          <button
            disabled={!canForkToTarget && !!forkPayload.target_project_id}
            onClick={async () => {
              setErr("");
              setMsg("");
              try {
                const res = await api.forkExperiment(
                  forkPayload.source_experiment_id,
                  forkPayload.target_project_id
                );
                setMsg(`Forked -> ${res.forked_experiment_id}`);
                refreshPosts();
              } catch (e) {
                setErr(e.message);
              }
            }}
          >
            Fork
          </button>
        </div>
        {!!forkPayload.target_project_id && (
          <PermissionHint role={forkTargetRole} action="edit" />
        )}
      </div>

      {msg && <p className="ok">{msg}</p>}
      {err && <p className="error">{err}</p>}
    </div>
  );
}
