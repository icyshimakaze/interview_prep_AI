"use client";

import { Overview } from "./workspace/overview";
import { EvidenceView } from "./workspace/evidence-view";
import {
  AssessmentsView,
  InterviewsView,
  ProgressView,
  RoadmapView,
} from "./workspace/history-view";
import { PersonalRoadmap } from "./workspace/personal-roadmap";
import { ProgressAnalytics } from "./workspace/progress-analytics";
import { ProjectsWorkspace } from "./workspace/projects-workspace";
import { SettingsView } from "./workspace/settings-view";
import type { WorkspaceContextValue } from "./workspace/workspace-context";
import type { WorkspaceSection } from "./workspace/navigation";
import { TargetJobsView } from "./workspace/target-jobs-view";
import { ResumeView } from "./workspace/resume-view";
import { SkillMatrixView } from "./workspace/skill-matrix";
import { QuestionBankView } from "./workspace/question-bank-view";
import { SectionHeader } from "./workspace/section-header";
import { AssessmentsWorkspace } from "./workspace/assessments-view";
import { InterviewsWorkspace } from "./workspace/interviews-workspace";

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
      return workspace.interviewApi ? (
        <InterviewsWorkspace api={workspace.interviewApi} />
      ) : (
        <InterviewsView data={data} />
      );
    case "roadmap":
      return workspace.planningApi ? (
        <PersonalRoadmap api={workspace.planningApi} />
      ) : (
        <RoadmapView {...workspace} />
      );
    case "progress":
      return workspace.planningApi ? (
        <ProgressAnalytics api={workspace.planningApi} />
      ) : (
        <ProgressView data={data} />
      );
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
      return workspace.projectApi ? (
        <ProjectsWorkspace api={workspace.projectApi} />
      ) : (
        <SectionHeader
          title="Project Repository"
          eyebrow="Know your work"
          description="Project repositories are unavailable. Reload your workspace to try again."
        />
      );
    case "settings":
      return <SettingsView {...workspace} />;
  }
}
