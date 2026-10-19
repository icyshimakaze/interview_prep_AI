import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { InterviewSession } from "@/components/workspace/interview-session";
import { InterviewConfigure } from "@/components/workspace/interview-configure";
import { InterviewReviewView } from "@/components/workspace/interview-review";
import {
  parseInterview,
  type Interview,
  type InterviewApi,
  type InterviewOptions,
  type InterviewReview,
} from "@/lib/api/interviews";
import { WorkspaceError } from "@/lib/api/workspace";

const time = "2026-10-19T10:00:00Z";
function fixture(): Interview {
  return {
    id: "session-1",
    revision: 2,
    contract_version: "interview-v1",
    status: "active",
    phase: "answering",
    configuration: {
      target_id: null,
      interview_type: "backend",
      difficulty: "auto",
      question_count: 2,
    },
    provider: {
      name: "MockAIProvider",
      version: "mock-lexical-v1",
      kind: "simulation",
      model: null,
      disclosure: "Demo/simulated practice; not verified competence.",
    },
    target_title: null,
    started_at: time,
    deadline_at: "2026-10-20T10:00:00Z",
    ended_at: null,
    completed_at: null,
    end_reason: null,
    expired: false,
    server_time: time,
    current_turn: {
      id: "turn-1",
      sequence: 1,
      main_ordinal: 1,
      parent_id: null,
      kind: "bank",
      prompt: "Explain a safe retry strategy.",
      category: "Backend",
      difficulty: "medium",
      status: "awaiting_answer",
      answer_text: null,
      answer_revision: 1,
      answering_ms: 0,
      running_since: time,
      context_excerpt: null,
      evaluation_status: null,
    },
    followup_decision: "none",
    progress: {
      requested: 2,
      presented: 1,
      resolved: 0,
      answered: 0,
      skipped: 0,
      followups_reserved: 0,
      followups_presented: 0,
      evaluation_pending: 0,
      evaluation_failed: 0,
    },
    allowed_actions: ["save", "submit", "skip", "pause", "end"],
    notices: [],
  };
}
function apiFixture(): InterviewApi {
  return {
    options: vi.fn(),
    history: vi.fn(),
    create: vi.fn(),
    read: vi.fn().mockResolvedValue(fixture()),
    command: vi.fn(),
    review: vi.fn(),
  };
}
const options: InterviewOptions = {
  inventory: [
    {
      interview_type: "technical_fundamentals",
      label: "Technical Fundamentals",
      difficulty: "auto",
      available_count: 12,
      max_questions: 10,
      min_questions: 1,
    },
    {
      interview_type: "frontend",
      label: "Frontend",
      difficulty: "auto",
      available_count: 1,
      max_questions: 1,
      min_questions: 1,
    },
  ],
  provider: fixture().provider,
  targets: [],
  max_followups: 3,
  answer_limit: 10000,
  notices: ["Actual published inventory."],
};

describe("mock interviews", () => {
  it("offers one explicit retry for an unavailable current evaluation", async () => {
    const user = userEvent.setup(),
      initial = fixture(),
      api = apiFixture();
    const failed: Interview = {
      ...initial,
      phase: "between_questions",
      allowed_actions: ["retry_evaluation", "end"],
      current_turn: initial.current_turn
        ? {
            ...initial.current_turn,
            status: "evaluation_failed",
            answer_text: "Saved response",
            evaluation_id: "failed-evaluation",
            evaluation_version: 1,
            evaluation_status: "failed",
          }
        : null,
    };
    vi.mocked(api.command).mockResolvedValue({
      ...failed,
      allowed_actions: ["end"],
      revision: 3,
    });
    render(<InterviewSession initial={failed} api={api} onBack={vi.fn()} />);
    await user.click(
      screen.getByRole("button", { name: "Retry unavailable evaluation once" }),
    );
    expect(api.command).toHaveBeenCalledWith(
      "session-1",
      "turns/turn-1/evaluation/retry",
      expect.objectContaining({ evaluation_id: "failed-evaluation" }),
      "POST",
    );
    expect(screen.getByLabelText("Your answer")).toHaveValue("Saved response");
  });
  it("configures all seven types from real availability and discloses simulation", async () => {
    const user = userEvent.setup(),
      onCreate = vi.fn();
    render(
      <InterviewConfigure options={options} busy={false} onCreate={onCreate} />,
    );
    expect(
      screen
        .getAllByRole("option")
        .some((o) => o.textContent === "System Design"),
    ).toBe(true);
    expect(screen.getByText(/Demo\/simulated practice/)).toBeInTheDocument();
    await user.selectOptions(
      screen.getByLabelText("Interview type"),
      "frontend",
    );
    expect(screen.getByLabelText("Main questions")).toHaveValue(1);
    await user.click(screen.getByRole("button", { name: "Start interview" }));
    expect(onCreate).toHaveBeenCalledWith({
      target_id: null,
      interview_type: "frontend",
      difficulty: "auto",
      question_count: 1,
    });
  });
  it("retains text after a failed submission and replays its exact key", async () => {
    const user = userEvent.setup(),
      api = apiFixture(),
      initial = fixture();
    const submitted: Interview = {
      ...initial,
      revision: 3,
      phase: "between_questions",
      allowed_actions: ["advance_main", "followup", "end"],
      current_turn: initial.current_turn
        ? {
            ...initial.current_turn,
            answer_text: "Saved retry answer",
            status: "submitted",
          }
        : null,
    };
    vi.mocked(api.command)
      .mockRejectedValueOnce(new Error("Connection lost"))
      .mockResolvedValue(submitted);
    render(<InterviewSession initial={initial} api={api} onBack={vi.fn()} />);
    await user.type(screen.getByLabelText("Your answer"), "Saved retry answer");
    await user.click(screen.getByRole("button", { name: "Submit answer" }));
    expect(await screen.findByText("Connection lost")).toBeInTheDocument();
    expect(screen.getByLabelText("Your answer")).toHaveValue(
      "Saved retry answer",
    );
    await user.click(
      screen.getByRole("button", { name: "Retry same request" }),
    );
    await screen.findByRole("button", { name: "Next main question" });
    expect(vi.mocked(api.command).mock.calls[0]).toEqual(
      vi.mocked(api.command).mock.calls[1],
    );
  });
  it("refreshes a worker-only revision conflict without overwriting another draft", async () => {
    const user = userEvent.setup(),
      api = apiFixture(),
      initial = fixture();
    vi.mocked(api.command)
      .mockRejectedValueOnce(
        new WorkspaceError("Worker changed revision", "interview_revision"),
      )
      .mockResolvedValue({
        ...initial,
        revision: 4,
        status: "paused",
        allowed_actions: ["resume", "end"],
      });
    vi.mocked(api.read).mockResolvedValue({ ...initial, revision: 3 });
    render(<InterviewSession initial={initial} api={api} onBack={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Pause interview" }));
    await screen.findByRole("button", { name: "Resume interview" });
    expect(vi.mocked(api.command).mock.calls[1]?.[2].revision).toBe(3);
    expect(vi.mocked(api.command).mock.calls[1]?.[2].command_key).not.toBe(
      vi.mocked(api.command).mock.calls[0]?.[2].command_key,
    );
  });
  it("does not show next/submit controls on a paused session and restores saved text", () => {
    const initial = fixture();
    render(
      <InterviewSession
        initial={{
          ...initial,
          status: "paused",
          allowed_actions: ["resume", "end"],
          current_turn: initial.current_turn
            ? {
                ...initial.current_turn,
                answer_text: "Saved before interruption",
                running_since: null,
              }
            : null,
        }}
        api={apiFixture()}
        onBack={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Your answer")).toHaveValue(
      "Saved before interruption",
    );
    expect(
      screen.queryByRole("button", { name: "Submit answer" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Resume interview" }),
    ).toBeInTheDocument();
  });
  it("keeps navigation available while optional follow-up generation is pending", () => {
    const initial = fixture();
    render(
      <InterviewSession
        initial={{
          ...initial,
          phase: "followup_pending",
          followup_decision: "pending",
          allowed_actions: ["advance_main", "end", "pause"],
          current_turn: initial.current_turn
            ? {
                ...initial.current_turn,
                status: "submitted",
                answer_text: "Submitted",
              }
            : null,
        }}
        api={apiFixture()}
        onBack={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Continue without follow-up" }),
    ).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: "Ask a follow-up" }),
    ).not.toBeInTheDocument();
  });
  it("renders partial final review with retained answer and an unavailable evaluation", () => {
    const session = fixture();
    const review: InterviewReview = {
      session: {
        ...session,
        status: "abandoned",
        end_reason: "early",
        allowed_actions: ["review"],
        progress: { ...session.progress, answered: 1, evaluation_failed: 1 },
      },
      review_status: "final",
      evaluation_coverage: "none",
      submitted_main: 1,
      evaluated_main: 0,
      unasked_main: 1,
      notices: ["No readiness score."],
      turns: session.current_turn
        ? [
            {
              turn: {
                ...session.current_turn,
                answer_text: "Retained response",
                status: "evaluation_failed",
              },
              expected_concepts: [],
              rubric: [],
              rationale: null,
              evaluation: {
                id: "evaluation-1",
                version: 1,
                status: "failed",
                kind: "simulation",
                score: null,
                score_scale_max: 4,
                feedback: null,
                error_code: "ai_timeout",
                provider: "MockAIProvider",
                model: null,
                prompt_version: "ai-prompts-v1",
              },
            },
          ]
        : [],
    };
    render(<InterviewReviewView review={review} />);
    expect(screen.getByText("Retained response")).toBeInTheDocument();
    expect(screen.getByText(/Evaluation unavailable/)).toBeInTheDocument();
    expect(screen.queryByText(/score: 0/)).not.toBeInTheDocument();
  });
  it("rejects hidden feedback accidentally included in the current-turn response", () => {
    const session = fixture();
    expect(() =>
      parseInterview({
        ...session,
        current_turn: { ...session.current_turn, score: 4 },
      }),
    ).toThrow(/hints before review/);
  });
  it("autosaves a draft without advancing the current question", async () => {
    const user = userEvent.setup(),
      api = apiFixture(),
      initial = fixture();
    vi.mocked(api.command).mockImplementation(async (_id, _action, body) => ({
      ...initial,
      revision: 3,
      current_turn: initial.current_turn
        ? { ...initial.current_turn, answer_text: body.answer_text ?? null }
        : null,
    }));
    render(<InterviewSession initial={initial} api={api} onBack={vi.fn()} />);
    await user.type(screen.getByLabelText("Your answer"), "Autosaved draft");
    await waitFor(() => expect(api.command).toHaveBeenCalled(), {
      timeout: 3000,
    });
    expect(vi.mocked(api.command).mock.calls[0]?.[1]).toBe(
      "turns/turn-1/draft",
    );
    expect(
      screen.getByRole("heading", { name: "Explain a safe retry strategy." }),
    ).toBeInTheDocument();
  });
});
