"use client";

import RoleBadge from "@/components/RoleBadge";

export default function PermissionHint({ role, action = "edit" }) {
  const normalized = String(role || "").toLowerCase();
  const canEdit = normalized === "owner" || normalized === "editor";
  const canView = normalized === "owner" || normalized === "editor" || normalized === "viewer";
  const allowed = action === "view" ? canView : canEdit;
  const message = allowed
    ? `${action} allowed`
    : `${action} restricted (owner/editor required)`;

  return (
    <div className={`permission-hint ${allowed ? "ok" : "warn"}`}>
      <RoleBadge role={role} />
      <span>{message}</span>
    </div>
  );
}
