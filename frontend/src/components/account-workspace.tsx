"use client";

import { UserButton, useAuth, useClerk } from "@clerk/nextjs";
import {
  useCallback,
  useEffect,
  useRef,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { ButtonLink } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import { WorkspaceShell } from "@/components/workspace/workspace-shell";
import { WorkspaceContext } from "@/components/workspace/workspace-context";
import {
  parseDashboard,
  workspaceRequest,
  type Dashboard,
  type ProfileInput,
} from "@/lib/api/workspace";
import { createTargetApi, type TargetApi } from "@/lib/api/targets";
import { createSkillApi } from "@/lib/api/skills";
import { createQuestionApi } from "@/lib/api/questions";
import { createAssessmentApi, type AssessmentApi } from "@/lib/api/assessments";
import { createPlanningApi } from "@/lib/api/planning";
import { createProjectApi } from "@/lib/api/projects";
import { createInterviewApi } from "@/lib/api/interviews";
import { createAIReviewApi } from "@/lib/api/ai-review";
import {
  createResumeApi,
  type ResumeApi,
  type Resume,
} from "@/lib/api/resumes";

export function AccountWorkspace({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, userId } = useAuth();
  if (!isLoaded)
    return (
      <WorkspaceShell mode="account">
        <WorkspaceSkeleton label="Checking your session…" />
      </WorkspaceShell>
    );
  if (!isSignedIn || !userId)
    return (
      <WorkspaceShell mode="account">
        <h1 className="page-title mb-6">Sign in to your workspace</h1>
        <ButtonLink href="/sign-in">Sign in</ButtonLink>
      </WorkspaceShell>
    );
  // A subject change remounts all private data, forms and pending UI state.
  return <ClerkAccountSession key={userId}>{children}</ClerkAccountSession>;
}

function ClerkAccountSession({ children }: { children: ReactNode }) {
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const getAPIToken = useCallback(
    () => getToken({ template: "interview-prep-api" }),
    [getToken],
  );
  return (
    <AccountSession
      getToken={getAPIToken}
      signOut={signOut}
      userControl={<UserButton />}
    >
      {children}
    </AccountSession>
  );
}

export function AccountSession({
  children,
  getToken,
  signOut,
  userControl,
  onSignedOut,
}: {
  children: ReactNode;
  getToken: () => Promise<string | null>;
  signOut: () => Promise<void>;
  userControl: ReactNode;
  onSignedOut?: () => void;
}) {
  const router = useRouter();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  const authenticatedRequest = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const token = await getToken();
      if (!active.current)
        throw new Error(
          "Your account changed. Open your current workspace again.",
        );
      if (!token) throw new Error("Sign in again to open your workspace.");
      const headers = new Headers(init.headers);
      headers.set("Authorization", `Bearer ${token}`);
      return workspaceRequest(path, { ...init, headers });
    },
    [getToken],
  );
  const planningApi = useMemo(
    () => ({
      ai: {
        options: () => createAIReviewApi(authenticatedRequest).options(),
        review: (
          ...args: Parameters<ReturnType<typeof createAIReviewApi>["review"]>
        ) => createAIReviewApi(authenticatedRequest).review(...args),
      },
      read: (
        ...args: Parameters<ReturnType<typeof createPlanningApi>["read"]>
      ) => createPlanningApi(authenticatedRequest, "account").read(...args),
      generate: (
        ...args: Parameters<ReturnType<typeof createPlanningApi>["generate"]>
      ) => createPlanningApi(authenticatedRequest, "account").generate(...args),
      change: (
        ...args: Parameters<ReturnType<typeof createPlanningApi>["change"]>
      ) => createPlanningApi(authenticatedRequest, "account").change(...args),
      progress: (
        ...args: Parameters<ReturnType<typeof createPlanningApi>["progress"]>
      ) => createPlanningApi(authenticatedRequest, "account").progress(...args),
    }),
    [authenticatedRequest],
  );
  const projectApi = useMemo(
    () => ({
      ai: {
        options: () => createAIReviewApi(authenticatedRequest).options(),
        review: (
          ...args: Parameters<ReturnType<typeof createAIReviewApi>["review"]>
        ) => createAIReviewApi(authenticatedRequest).review(...args),
      },
      list: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["list"]>
      ) => createProjectApi(authenticatedRequest, "account").list(...args),
      read: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["read"]>
      ) => createProjectApi(authenticatedRequest, "account").read(...args),
      github: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["github"]>
      ) => createProjectApi(authenticatedRequest, "account").github(...args),
      upload: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["upload"]>
      ) => createProjectApi(authenticatedRequest, "account").upload(...args),
      example: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["example"]>
      ) => createProjectApi(authenticatedRequest, "account").example(...args),
      remove: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["remove"]>
      ) => createProjectApi(authenticatedRequest, "account").remove(...args),
      history: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["history"]>
      ) => createProjectApi(authenticatedRequest, "account").history(...args),
      start: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["start"]>
      ) => createProjectApi(authenticatedRequest, "account").start(...args),
      readRun: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["readRun"]>
      ) => createProjectApi(authenticatedRequest, "account").readRun(...args),
      command: (
        ...args: Parameters<ReturnType<typeof createProjectApi>["command"]>
      ) => createProjectApi(authenticatedRequest, "account").command(...args),
    }),
    [authenticatedRequest],
  );
  const skillApi = useMemo(
    () => ({
      read: (target: string | null, signal?: AbortSignal) =>
        createSkillApi(authenticatedRequest, "account").read(target, signal),
    }),
    [authenticatedRequest],
  );
  const questionApi = useMemo(
    () => ({
      list: (
        ...args: Parameters<ReturnType<typeof createQuestionApi>["list"]>
      ) => createQuestionApi(authenticatedRequest, "account").list(...args),
      facets: (
        ...args: Parameters<ReturnType<typeof createQuestionApi>["facets"]>
      ) => createQuestionApi(authenticatedRequest, "account").facets(...args),
      read: (
        ...args: Parameters<ReturnType<typeof createQuestionApi>["read"]>
      ) => createQuestionApi(authenticatedRequest, "account").read(...args),
      bookmark: (
        ...args: Parameters<ReturnType<typeof createQuestionApi>["bookmark"]>
      ) => createQuestionApi(authenticatedRequest, "account").bookmark(...args),
      submit: (
        ...args: Parameters<ReturnType<typeof createQuestionApi>["submit"]>
      ) => createQuestionApi(authenticatedRequest, "account").submit(...args),
      history: (
        ...args: Parameters<ReturnType<typeof createQuestionApi>["history"]>
      ) => createQuestionApi(authenticatedRequest, "account").history(...args),
      removeAttempt: (
        ...args: Parameters<
          ReturnType<typeof createQuestionApi>["removeAttempt"]
        >
      ) =>
        createQuestionApi(authenticatedRequest, "account").removeAttempt(
          ...args,
        ),
    }),
    [authenticatedRequest],
  );
  const interviewApi = useMemo(
    () => ({
      options: (
        ...args: Parameters<ReturnType<typeof createInterviewApi>["options"]>
      ) => createInterviewApi(authenticatedRequest, "account").options(...args),
      history: (
        ...args: Parameters<ReturnType<typeof createInterviewApi>["history"]>
      ) => createInterviewApi(authenticatedRequest, "account").history(...args),
      create: (
        ...args: Parameters<ReturnType<typeof createInterviewApi>["create"]>
      ) => createInterviewApi(authenticatedRequest, "account").create(...args),
      read: (
        ...args: Parameters<ReturnType<typeof createInterviewApi>["read"]>
      ) => createInterviewApi(authenticatedRequest, "account").read(...args),
      command: (
        ...args: Parameters<ReturnType<typeof createInterviewApi>["command"]>
      ) => createInterviewApi(authenticatedRequest, "account").command(...args),
      review: (
        ...args: Parameters<ReturnType<typeof createInterviewApi>["review"]>
      ) => createInterviewApi(authenticatedRequest, "account").review(...args),
    }),
    [authenticatedRequest],
  );
  const assessmentApi = useMemo<AssessmentApi>(
    () => ({
      options: (...args) =>
        createAssessmentApi(authenticatedRequest, "account").options(...args),
      history: (...args) =>
        createAssessmentApi(authenticatedRequest, "account").history(...args),
      read: (...args) =>
        createAssessmentApi(authenticatedRequest, "account").read(...args),
      start: (...args) =>
        createAssessmentApi(authenticatedRequest, "account").start(...args),
      save: (...args) =>
        createAssessmentApi(authenticatedRequest, "account").save(...args),
      submit: (...args) =>
        createAssessmentApi(authenticatedRequest, "account").submit(...args),
      abandon: (...args) =>
        createAssessmentApi(authenticatedRequest, "account").abandon(...args),
    }),
    [authenticatedRequest],
  );
  const readDashboard = useCallback(
    async (signal?: AbortSignal) => {
      const result = parseDashboard(
        await (
          await authenticatedRequest("/api/v1/account/dashboard", { signal })
        ).json(),
      );
      if (result.mode !== "account")
        throw new Error("The account workspace response is invalid.");
      return result;
    },
    [authenticatedRequest],
  );
  const targetApi = useMemo<TargetApi>(() => {
    return {
      ai: {
        options: () => createAIReviewApi(authenticatedRequest).options(),
        review: (
          ...args: Parameters<ReturnType<typeof createAIReviewApi>["review"]>
        ) => createAIReviewApi(authenticatedRequest).review(...args),
      },
      list: (offset, status, signal) =>
        createTargetApi(authenticatedRequest).list(offset, status, signal),
      read: (id) => createTargetApi(authenticatedRequest).read(id),
      save: async (input, target) => {
        const result = await createTargetApi(authenticatedRequest).save(
          input,
          target,
        );
        setData((current) =>
          current
            ? {
                ...current,
                targets: [
                  result,
                  ...current.targets.filter((item) => item.id !== result.id),
                ].slice(0, 10),
              }
            : current,
        );
        return result;
      },
      remove: async (target) => {
        await createTargetApi(authenticatedRequest).remove(target);
        setData((current) =>
          current
            ? {
                ...current,
                targets: current.targets.filter(
                  (item) => item.id !== target.id,
                ),
              }
            : current,
        );
      },
    };
  }, [authenticatedRequest]);
  const resumeApi = useMemo<ResumeApi>(() => {
    const update = async (operation: Promise<Resume>) => {
      const result = await operation;
      setData((current) =>
        current
          ? {
              ...current,
              resumes: [
                {
                  id: result.id,
                  label: result.label,
                  evidence: result.evidence
                    .filter((item) => item.review_status !== "rejected")
                    .map(
                      (item) =>
                        item.user_correction ??
                        item.source_excerpt ??
                        item.claim,
                    ),
                },
                ...current.resumes.filter((item) => item.id !== result.id),
              ].slice(0, 10),
            }
          : current,
      );
      return result;
    };
    return {
      ai: {
        options: () => createAIReviewApi(authenticatedRequest).options(),
        review: (
          ...args: Parameters<ReturnType<typeof createAIReviewApi>["review"]>
        ) => createAIReviewApi(authenticatedRequest).review(...args),
      },
      list: (signal) => createResumeApi(authenticatedRequest).list(signal),
      read: (id) => createResumeApi(authenticatedRequest).read(id),
      upload: (file) =>
        update(createResumeApi(authenticatedRequest).upload(file)),
      saveEvidence: (resume, input, evidence) =>
        update(
          createResumeApi(authenticatedRequest).saveEvidence(
            resume,
            input,
            evidence,
          ),
        ),
      removeEvidence: (resume, evidence) =>
        update(
          createResumeApi(authenticatedRequest).removeEvidence(
            resume,
            evidence,
          ),
        ),
      remove: async (resume) => {
        await createResumeApi(authenticatedRequest).remove(resume);
        setData((current) =>
          current
            ? {
                ...current,
                resumes: current.resumes.filter(
                  (item) => item.id !== resume.id,
                ),
              }
            : current,
        );
      },
    };
  }, [authenticatedRequest]);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const load = async () => {
      await authenticatedRequest("/api/v1/account/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
        signal: controller.signal,
      });
      const result = await readDashboard(controller.signal);
      if (active) setData(result);
    };
    void load().catch((reason: unknown) => {
      if (active)
        setError(
          reason instanceof Error
            ? reason.message
            : "Your workspace could not load.",
        );
    });
    return () => {
      active = false;
      controller.abort();
    };
  }, [authenticatedRequest, readDashboard, attempt]);
  function reload() {
    setData(null);
    setError(null);
    setAttempt((value) => value + 1);
  }
  async function saveProfile(profile: ProfileInput) {
    setBusy(true);
    try {
      await authenticatedRequest("/api/v1/account/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      try {
        setData(await readDashboard());
      } catch {
        throw new Error(
          "Your save was accepted, but the updated profile could not be loaded. Reload the saved profile before editing again.",
        );
      }
    } finally {
      setBusy(false);
    }
  }
  async function leave() {
    setBusy(true);
    setData(null);
    setError(null);
    try {
      await signOut();
      if (onSignedOut) onSignedOut();
      else {
        router.replace("/");
        router.refresh();
      }
    } catch {
      setError("Sign-out could not complete. Please try again.");
      setBusy(false);
    }
  }
  async function deleteProfile() {
    if (!data?.profile)
      throw new Error("Reload your profile before deleting it.");
    setBusy(true);
    try {
      await authenticatedRequest(
        `/api/v1/account/profile?expected_id=${encodeURIComponent(data.profile.id)}&expected_revision=${data.profile.revision}`,
        { method: "DELETE" },
      );
      setData((current) => (current ? { ...current, profile: null } : current));
    } finally {
      setBusy(false);
    }
  }
  return (
    <WorkspaceShell
      mode="account"
      onLeave={() => void leave()}
      busy={busy}
      userControl={userControl}
    >
      {error && (
        <ErrorDisplay
          title="Your workspace needs attention"
          message={error}
          onRetry={reload}
        />
      )}
      {data ? (
        <WorkspaceContext
          value={{
            data,
            busy,
            onSaveProfile: saveProfile,
            onDeleteProfile: deleteProfile,
            targetApi,
            resumeApi,
            skillApi,
            questionApi,
            assessmentApi,
            interviewApi,
            projectApi,
            planningApi,
            onReload: reload,
          }}
        >
          {children}
        </WorkspaceContext>
      ) : (
        !error && (
          <WorkspaceSkeleton label={busy ? "Signing out…" : undefined} />
        )
      )}
    </WorkspaceShell>
  );
}
