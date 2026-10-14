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
import { SkillMatrixView } from "./workspace/skill-matrix";
import { QuestionBankView } from "./workspace/question-bank-view";
import { SectionHeader } from "./workspace/section-header";
import { AssessmentsWorkspace } from "./workspace/assessments-view";

export function WorkspaceView({
  section = "dashboard",
  ...workspace
}: WorkspaceContextValue & { section?: WorkspaceSection }) {
  const { data } = workspace;
  switch (section) {
    case "skills":
      return workspace.skillApi ? (
        <SkillMatrixView api={workspace.skillApi} />
      ) : (
        <SectionHeader
          title="Skill Matrix"
          eyebrow="Evidence, explained"
          description="Skill evidence is unavailable. Reload your workspace to try again."
        />
      );
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
      return workspace.assessmentApi ? (
        <AssessmentsWorkspace api={workspace.assessmentApi} />
      ) : (
        <AssessmentsView data={data} />
      );
    case "interviews":
      return <InterviewsView data={data} />;
    case "roadmap":
      return <RoadmapView {...workspace} />;
    case "progress":
      return <ProgressView data={data} />;
    case "questions":
      return workspace.questionApi ? (
        <QuestionBankView api={workspace.questionApi} mode={data.mode} />
      ) : (
        <SectionHeader
          title="Question Bank"
          eyebrow="Focused practice"
          description="Question browsing is unavailable. Reload your workspace to try again."
        />
      );
    case "projects":
      return <PlannedView mode={data.mode} section={section} />;
    case "settings":
      return <SettingsView {...workspace} />;
  }
}
