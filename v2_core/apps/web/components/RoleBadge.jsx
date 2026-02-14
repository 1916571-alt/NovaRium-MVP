"use client";

export default function RoleBadge({ role }) {
  const normalized = String(role || "").toLowerCase();
  let cls = "role-badge";
  if (normalized === "owner") cls += " owner";
  else if (normalized === "editor") cls += " editor";
  else if (normalized === "viewer") cls += " viewer";
  else cls += " none";

  return (
    <span className={cls}>
      role: {normalized || "not-member"}
    </span>
  );
}
