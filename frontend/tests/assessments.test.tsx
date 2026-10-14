import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AssessmentAttemptView } from "@/components/workspace/assessment-attempt";
import { AssessmentsWorkspace } from "@/components/workspace/assessments-view";
import {
  createAssessmentApi,
  parseAssessment,
  parseAssessmentPage,
} from "@/lib/api/assessments";
import {
  assessmentApiFixture,
  assessmentFixture,
  completedAssessment,
} from "./assessment-fixture";

describe("real assessments", () => {
  it("configures from actual inventory and applies difficulty and question formats", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup();
    render(<AssessmentsWorkspace api={api} />);
    await screen.findByText(/4 published questions match/);
    await user.selectOptions(
      screen.getByLabelText("Assessment difficulty"),
      "hard",
    );
    expect(
      screen.getByRole("button", { name: "Start assessment" }),
    ).toBeDisabled();
    await user.clear(screen.getByLabelText("Number of questions"));
    await user.type(screen.getByLabelText("Number of questions"), "1");
    await user.selectOptions(
      screen.getByLabelText("Assessment category"),
      "DBMS",
    );
    await user.click(screen.getByLabelText("MCQ · choose one"));
    await user.click(screen.getByRole("button", { name: "Start assessment" }));
    await waitFor(() =>
      expect(api.start).toHaveBeenCalledWith(
        expect.objectContaining({
          difficulty: "hard",
          category: "DBMS",
          question_count: 1,
          question_types: ["multiple_select", "short_answer", "written"],
        }),
      ),
    );
  });

  it("reuses the start key after a network error and paginates history", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup();
    api.start = vi
      .fn()
      .mockRejectedValueOnce(new Error("Network unavailable"))
      .mockResolvedValueOnce(assessmentFixture);
    render(<AssessmentsWorkspace api={api} />);
    await screen.findByRole("button", { name: "Start assessment" });
    await user.click(screen.getByRole("button", { name: "Next page" }));
    await waitFor(() =>
      expect(api.history).toHaveBeenLastCalledWith(10, expect.any(AbortSignal)),
    );
    await user.click(screen.getByRole("button", { name: "Start assessment" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Network unavailable",
    );
    await user.click(screen.getByRole("button", { name: "Start assessment" }));
    await screen.findByText("Index lookup");
    const calls = vi.mocked(api.start).mock.calls;
    expect(calls[0]?.[0].submission_key).toBe(calls[1]?.[0].submission_key);
  });

  it("resumes unfinished history, saves before navigation, selects multiple answers, and reviews separate results", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup();
    render(<AssessmentsWorkspace api={api} />);
    await user.click(
      await screen.findByRole("button", { name: "Resume DBMS assessment" }),
    );
    expect(screen.queryByText("Expected concepts")).not.toBeInTheDocument();
    await user.click(screen.getByLabelText("Selective equality lookup"));
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(api.save).toHaveBeenCalledWith(
      "attempt-one",
      "q1",
      expect.objectContaining({ revision: 1, selected_option_ids: ["o1"] }),
    );
    await user.click(screen.getByLabelText("Atomic changes"));
    await user.click(screen.getByLabelText("Durable commits"));
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.type(
      screen.getByLabelText("Your answer"),
      "Writes maintain index entries.",
    );
    await user.click(screen.getByRole("button", { name: "Submit assessment" }));
    await screen.findByRole("heading", { name: "Category performance" });
    expect(api.submit).toHaveBeenCalledWith("attempt-one", 4);
    expect(screen.getByText("2 correct of 2")).toBeInTheDocument();
    expect(screen.getByText("2 of 4 · Mock simulation")).toBeInTheDocument();
    expect(
      screen.getByText(/lexical overlap is not demonstrated competence/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Submit assessment" }),
    ).not.toBeInTheDocument();
  });

  it("retains a response and position after a failed save and retries navigation", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup(),
      save = api.save;
    api.save = vi
      .fn()
      .mockRejectedValueOnce(new Error("Offline"))
      .mockImplementation(save);
    render(
      <AssessmentAttemptView
        initial={assessmentFixture}
        api={api}
        onBack={vi.fn()}
      />,
    );
    await user.click(screen.getByLabelText("Selective equality lookup"));
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Offline");
    expect(screen.getByLabelText("Selective equality lookup")).toBeChecked();
    expect(
      screen.queryByRole("heading", { name: "Transaction guarantees" }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(
      await screen.findByRole("heading", { name: "Transaction guarantees" }),
    ).toBeInTheDocument();
  });

  it("retries a lost submission response without resaving or losing answers", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup(),
      submit = api.submit;
    api.submit = vi
      .fn()
      .mockRejectedValueOnce(new Error("Response timed out"))
      .mockImplementation(submit);
    render(
      <AssessmentAttemptView
        initial={assessmentFixture}
        api={api}
        onBack={vi.fn()}
      />,
    );
    await user.click(screen.getByLabelText("Selective equality lookup"));
    await user.click(screen.getByRole("button", { name: "Submit assessment" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Response timed out",
    );
    await user.click(screen.getByRole("button", { name: "Submit assessment" }));
    await screen.findByRole("heading", { name: "Question review" });
    expect(api.save).toHaveBeenCalledTimes(1);
    expect(api.submit).toHaveBeenCalledTimes(2);
  });

  it("reloads a stale revision while retaining local edits", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup(),
      save = api.save;
    api.save = vi
      .fn()
      .mockRejectedValueOnce(new Error("Revision changed"))
      .mockImplementation(save);
    api.read = vi.fn().mockResolvedValue({ ...assessmentFixture, revision: 8 });
    render(
      <AssessmentAttemptView
        initial={assessmentFixture}
        api={api}
        onBack={vi.fn()}
      />,
    );
    await user.click(screen.getByLabelText("Selective equality lookup"));
    await user.click(screen.getByRole("button", { name: "Save response" }));
    await screen.findByRole("alert");
    await user.click(
      screen.getByRole("button", { name: "Reload saved attempt" }),
    );
    await screen.findByText(/Saved attempt reloaded/);
    expect(screen.getByLabelText("Selective equality lookup")).toBeChecked();
    await user.click(screen.getByRole("button", { name: "Save response" }));
    expect(api.save).toHaveBeenLastCalledWith(
      "attempt-one",
      "q1",
      expect.objectContaining({ revision: 8, selected_option_ids: ["o1"] }),
    );
  });

  it("disables expired attempts and preserves saved responses for inspection", () => {
    render(
      <AssessmentAttemptView
        initial={{ ...assessmentFixture, status: "expired" }}
        api={assessmentApiFixture()}
        onBack={vi.fn()}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("expired");
    expect(screen.getByLabelText("Selective equality lookup")).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: "Submit assessment" }),
    ).not.toBeInTheDocument();
  });

  it("abandons explicitly and saves current work before returning to history", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup(),
      back = vi.fn();
    render(
      <AssessmentAttemptView
        initial={assessmentFixture}
        api={api}
        onBack={back}
      />,
    );
    await user.click(screen.getByLabelText("Selective equality lookup"));
    await user.click(screen.getByRole("button", { name: "Abandon attempt" }));
    await waitFor(() =>
      expect(api.abandon).toHaveBeenCalledWith("attempt-one", 2),
    );
    expect(
      screen.queryByRole("button", { name: "Submit assessment" }),
    ).not.toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Back to assessments" }),
    );
    expect(back).toHaveBeenCalledOnce();
  });

  it("recovers from unavailable inventory", async () => {
    const api = assessmentApiFixture(),
      user = userEvent.setup();
    api.options = vi
      .fn()
      .mockRejectedValueOnce(new Error("Service unavailable"))
      .mockResolvedValueOnce({
        max_questions: 12,
        duration_hours: 24,
        conceptual_provider: "MockAIProvider",
        conceptual_kind: "simulation",
        inventory: [],
      });
    render(<AssessmentsWorkspace api={api} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Service unavailable",
    );
    await user.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText(/0 published questions match/);
    expect(
      screen.getByRole("button", { name: "Start assessment" }),
    ).toBeDisabled();
  });

  it("rejects premature reviews, invalid scores and malformed history", () => {
    expect(parseAssessment(assessmentFixture)).toEqual(assessmentFixture);
    const completed = completedAssessment(assessmentFixture);
    expect(() =>
      parseAssessment({ ...completed, status: "in_progress" }),
    ).toThrow(/before submission/);
    expect(() =>
      parseAssessment({
        ...completed,
        questions: completed.questions.map((q) => ({
          ...q,
          review: { ...q.review, score: 99 },
        })),
      }),
    ).toThrow(/score/);
    expect(() =>
      parseAssessment({ ...assessmentFixture, question_count: 2 }),
    ).toThrow(/allocation/);
    expect(() =>
      parseAssessmentPage({ items: [], total: 0, offset: 0, limit: 0 }),
    ).toThrow(/pagination/);
  });

  it("uses owner-bound routes, revision bodies and demo CSRF without answer keys", async () => {
    document.cookie = "interview_prep_csrf=assessment-csrf";
    const request = vi
        .fn()
        .mockResolvedValue({ json: async () => assessmentFixture }),
      api = createAssessmentApi(request, "demo");
    await api.save("attempt-one", "q1", {
      revision: 4,
      selected_option_ids: ["o1"],
    });
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/demo/assessments/attempt-one/questions/q1",
      expect.objectContaining({
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": "assessment-csrf",
        },
        body: JSON.stringify({ revision: 4, selected_option_ids: ["o1"] }),
      }),
    );
    await api.submit("attempt-one", 5);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/demo/assessments/attempt-one/submit",
      expect.objectContaining({ body: '{"revision":5}' }),
    );
    await createAssessmentApi(request, "account").read("attempt-one");
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/account/assessments/attempt-one",
      expect.anything(),
    );
    document.cookie = "interview_prep_csrf=; max-age=0";
  });
});
