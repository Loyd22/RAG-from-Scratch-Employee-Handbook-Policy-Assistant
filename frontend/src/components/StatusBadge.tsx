/*
  File: StatusBadge.tsx
  Purpose: Show the result verdict in a simple colored badge.
*/

type StatusBadgeProps = {
  verdict: "FOUND" | "NOT_FOUND";
};

/*
  Function: StatusBadge
  Purpose: Render a small badge for FOUND or NOT_FOUND.
*/
function StatusBadge({ verdict }: StatusBadgeProps) {
  const isFound = verdict === "FOUND";

  return (
    <span className={`status-badge ${isFound ? "found" : "not-found"}`}>
      {verdict}
    </span>
  );
}

export default StatusBadge;