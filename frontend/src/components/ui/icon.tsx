import type { ComponentProps } from "react";

const paths = {
  dashboard: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  target: "M4 7h16v13H4z M9 7V4h6v3 M4 12h16 M10 12v3h4v-3",
  resume: "M6 3h8l4 4v14H6z M14 3v5h4 M9 12h6 M9 16h6",
  assessments: "M9 4H5v17h14V4h-4 M9 3h6v4H9z M8 12l2 2 5-4 M8 18h7",
  interviews: "M4 4h16v12H9l-5 4z M8 8h8 M8 12h5",
  questions:
    "M3 5c3-1 6-1 9 1 3-2 6-2 9-1v15c-3-1-6-1-9 1-3-2-6-2-9-1z M12 6v15",
  roadmap:
    "M7 3v12a4 4 0 0 0 4 4h6 M4 6l3-3 3 3 M14 16l3 3-3 3 M17 4v6 M14 7h6",
  projects: "M3 7h7l2 2h9v12H3z M3 7V3h7l2 2h9v4 M9 13l-2 2 2 2 M15 13l2 2-2 2",
  progress: "M4 3v18h17 M8 16v-4 M13 16V8 M18 16V4",
  settings:
    "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M8 19v-2a4 4 0 0 1 8 0v2 M12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
  arrow: "M4 12h16 M14 6l6 6-6 6",
  check: "M5 12l4 4L19 6",
  close: "M6 6l12 12 M6 18 18 6",
  menu: "M4 6h16 M4 12h16 M4 18h16",
  lock: "M5 10h14v11H5z M8 10V7a4 4 0 0 1 8 0v3 M12 14v3",
  info: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M12 11v6 M12 7v1",
  search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6",
  exit: "M10 4H4v16h6 M10 12h11 M17 8l4 4-4 4",
} as const;

export type IconName = keyof typeof paths;

export function Icon({
  name,
  ...props
}: ComponentProps<"svg"> & { name: IconName }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      <path d={paths[name]} />
    </svg>
  );
}
