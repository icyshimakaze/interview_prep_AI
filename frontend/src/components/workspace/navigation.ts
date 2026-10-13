import type { IconName } from "@/components/ui/icon";

export const workspaceSections = [
  {
    slug: "dashboard",
    label: "Dashboard",
    icon: "dashboard",
    group: "Workspace",
  },
  { slug: "targets", label: "Target Job", icon: "target", group: "Prepare" },
  { slug: "resume", label: "Resume", icon: "resume", group: "Prepare" },
  {
    slug: "assessments",
    label: "Assessments",
    icon: "assessments",
    group: "Practice",
  },
  {
    slug: "interviews",
    label: "Interviews",
    icon: "interviews",
    group: "Practice",
  },
  {
    slug: "questions",
    label: "Question Bank",
    icon: "questions",
    group: "Practice",
  },
  { slug: "roadmap", label: "Roadmap", icon: "roadmap", group: "Reflect" },
  {
    slug: "projects",
    label: "Project Defense",
    icon: "projects",
    group: "Reflect",
  },
  { slug: "progress", label: "Progress", icon: "progress", group: "Reflect" },
  {
    slug: "settings",
    label: "Settings / Profile",
    icon: "settings",
    group: "Account",
  },
] as const satisfies readonly {
  slug: string;
  label: string;
  icon: IconName;
  group: string;
}[];

export type WorkspaceSection = (typeof workspaceSections)[number]["slug"];
export function isWorkspaceSection(value: string): value is WorkspaceSection {
  return workspaceSections.some((section) => section.slug === value);
}
export function sectionHref(
  mode: "account" | "demo",
  section: WorkspaceSection,
): string {
  return mode === "demo"
    ? section === "dashboard"
      ? "/demo"
      : `/demo/${section}`
    : `/app/${section}`;
}
