"use client";

import { Overview } from "./workspace/overview";
import { EvidenceView } from "./workspace/evidence-view";
import {
  AssessmentsView,
  InterviewsView,
  ProgressView,
  RoadmapView,
} from "./workspace/history-view";
import { PlannedView } from "./workspace/planned-view";
import { SettingsView } from "./workspace/settings-view";
import type { WorkspaceContextValue } from "./workspace/workspace-context";
import type { WorkspaceSection } from "./workspace/navigation";
import { TargetJobsView } from "./workspace/target-jobs-view";
import { ResumeView } from "./workspace/resume-view";

export function WorkspaceView({
  section = "dashboard",
  ...workspace
}: WorkspaceContextValue & { section?: WorkspaceSection }) {
  const { data } = workspace;
  switch (section) {
    case "dashboard":
      return <Overview data={data} />;
    case "targets":
      return data.mode === "account" && workspace.targetApi ? (
        <TargetJobsView api={workspace.targetApi} />
      ) : (
        <EvidenceView data={data} section="targets" />
      );
    case "resume":
      return data.mode === "account" && workspace.resumeApi ? (
        <ResumeView api={workspace.resumeApi} />
      ) : (
        <EvidenceView data={data} section={section} />
      );
    case "assessments":
      return <AssessmentsView data={data} />;
    case "interviews":
      return <InterviewsView data={data} />;
    case "roadmap":
      return <RoadmapView {...workspace} />;
    case "progress":
      return <ProgressView data={data} />;
    case "questions":
    case "projects":
      return <PlannedView mode={data.mode} section={section} />;
    case "settings":
      return <SettingsView {...workspace} />;
  }
}
