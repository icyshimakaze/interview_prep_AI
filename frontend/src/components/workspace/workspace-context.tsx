"use client";

import { createContext, useContext } from "react";
import type { Dashboard, ProfileInput } from "@/lib/api/workspace";
import type { TargetApi } from "@/lib/api/targets";
import type { ResumeApi } from "@/lib/api/resumes";
import { WorkspaceView } from "@/components/workspace-view";
import type { WorkspaceSection } from "./navigation";

export type WorkspaceContextValue = {
  data: Dashboard;
  busy: boolean;
  onComplete?: (id: string) => void;
  onSaveProfile?: (input: ProfileInput) => Promise<void>;
  onDeleteProfile?: () => Promise<void>;
  targetApi?: TargetApi;
  resumeApi?: ResumeApi;
  onReload?: () => void;
};
export const WorkspaceContext = createContext<WorkspaceContextValue | null>(
  null,
);

export function WorkspaceScreen({ section }: { section: WorkspaceSection }) {
  const workspace = useContext(WorkspaceContext);
  if (!workspace) throw new Error("Workspace data is unavailable.");
  return <WorkspaceView {...workspace} section={section} />;
}
