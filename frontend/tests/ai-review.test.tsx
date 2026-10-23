import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AIReview } from "@/components/workspace/ai-review";
import { AssessmentConfigure } from "@/components/workspace/assessment-configure";
import { InterviewConfigure } from "@/components/workspace/interview-configure";
import { createAIReviewApi, type AIReviewApi } from "@/lib/api/ai-review";
import { createProjectApi } from "@/lib/api/projects";
import { workspaceRequest } from "@/lib/api/workspace";
import { assessmentOptions } from "./assessment-fixture";
import type { InterviewOptions } from "@/lib/api/interviews";

function fixture(
  kind: "simulation" | "model_assisted" = "model_assisted",
): AIReviewApi {
  return {
    options: vi.fn().mockResolvedValue({
      name: kind === "simulation" ? "MockAIProvider" : "XkiroProvider",
      version: "test-v1",
      kind,
      disclosure:
        "Requesting review sends retained resume claims/excerpts to xKiro and its downstream provider. Third-party retention policies apply.",
    }),
    review: vi.fn().mockResolvedValue({
      summary: "Clarify your contribution.",
      suggestions: ["Describe a failure case."],
      provider: kind === "simulation" ? "MockAIProvider" : "XkiroProvider",
      model: kind === "simulation" ? null : "qwen/qwen3.8-max:free",
      kind,
      disclosure: "Requires human review.",
    }),
  };
}

describe("opt-in AI reviews", () => {
  it.each([
    [
      "targets/1",
      {
        summary: "Backend role",
        review_notes: ["Discuss transactions"],
        requirements: [
          { name: "SQL", importance: "required", evidence: "SQL required" },
        ],
      },
      "SQL (required): SQL required",
    ],
    [
      "roadmaps/1",
      {
        summary: "Practice from saved results",
        steps: [
          {
            topic: "SQL",
            minutes: 20,
            activity: "Test a transaction",
            success_check: "Explain rollback",
          },
        ],
      },
      "SQL (20 minutes): Test a transaction Check: Explain rollback",
    ],
    [
      "projects/1",
      {
        questions: [
          {
            question: "How would you test a failed write?",
            focus: "Testing",
            evidence: "Observed database",
          },
        ],
      },
      "Testing: How would you test a failed write? Evidence: Observed database",
    ],
  ])(
    "parses source-backed %s suggestions and preserves provenance",
    async (resource, data, expected) => {
      const request = vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            data,
            provenance: {
              provider: "XkiroProvider",
              model: "qwen/qwen3.8-max:free",
              kind: "model_assisted",
              disclosure: "Requires review",
            },
          }),
        ),
      );
      const result = await createAIReviewApi(request).review(
        resource,
        "version",
      );
      expect(result.suggestions).toContain(expected);
      expect(result.kind).toBe("model_assisted");
      expect(request).toHaveBeenCalledExactlyOnceWith(
        `/api/v1/account/ai/${resource}`,
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ consent: true, provider_version: "version" }),
        }),
      );
    },
  );

  it("does not dispatch a review again when rerendered", async () => {
    const api = fixture(),
      user = userEvent.setup();
    const view = render(
      <AIReview
        api={api}
        resource="projects/1"
        label="Generate project practice questions"
      />,
    );
    await user.click(
      screen.getByRole("button", {
        name: "Generate project practice questions",
      }),
    );
    await user.click(screen.getByRole("checkbox"));
    await user.click(
      screen.getByRole("button", {
        name: "Request generate project practice questions",
      }),
    );
    await screen.findByText("Clarify your contribution.");
    view.rerender(
      <AIReview
        api={api}
        resource="projects/1"
        label="Generate project practice questions"
      />,
    );
    expect(api.review).toHaveBeenCalledTimes(1);
  });
  it.each([
    ["ai_rate_limited", /rate limit was reached/],
    ["ai_timeout", /timed out/],
    ["ai_invalid_output", /failed validation/],
    ["ai_analysis_pending", /no duplicate AI call was sent/],
    ["ai_provider_changed", /Reload before agreeing to share/],
  ])(
    "shows safe actionable %s errors from the real request client",
    async (code, message) => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(
          JSON.stringify({ code, message: "PRIVATE UPSTREAM CONTENT" }),
          {
            status:
              code === "ai_provider_changed" || code === "ai_analysis_pending"
                ? 409
                : 503,
          },
        ),
      );
      const request = workspaceRequest("/api/v1/account/ai/resumes/id");
      await expect(request).rejects.toThrow(message);
      await expect(request).rejects.not.toThrow(/PRIVATE UPSTREAM CONTENT/);
    },
  );

  it("shares nothing until explicit disclosure, consent and review request", async () => {
    const api = fixture(),
      user = userEvent.setup();
    render(
      <AIReview
        api={api}
        resource="resumes/resume-1"
        label="Review resume evidence"
      />,
    );
    expect(api.options).not.toHaveBeenCalled();
    expect(api.review).not.toHaveBeenCalled();
    await user.click(
      screen.getByRole("button", { name: "Review resume evidence" }),
    );
    expect(
      await screen.findByText(/Third-party retention policies apply/),
    ).toBeInTheDocument();
    const request = screen.getByRole("button", {
      name: "Request review resume evidence",
    });
    expect(request).toBeDisabled();
    expect(
      screen.getByRole("checkbox", { name: /I agree to send/ }),
    ).toHaveFocus();
    expect(api.review).not.toHaveBeenCalled();
    await user.click(screen.getByRole("checkbox", { name: /I agree to send/ }));
    await user.click(request);
    expect(api.review).toHaveBeenCalledExactlyOnceWith(
      "resumes/resume-1",
      "test-v1",
    );
    expect(await screen.findByText(/AI-assisted review/)).toHaveFocus();
    expect(screen.getByText("Clarify your contribution.")).toBeInTheDocument();
    expect(screen.getByText(/Saved for reuse/)).toBeInTheDocument();
  });

  it("labels deterministic simulation without presenting it as real AI", async () => {
    const user = userEvent.setup();
    render(
      <AIReview
        api={fixture("simulation")}
        resource="resumes/1"
        label="Review resume evidence"
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Review resume evidence" }),
    );
    await user.click(
      await screen.findByRole("checkbox", {
        name: /deterministic mock simulation/,
      }),
    );
    await user.click(
      screen.getByRole("button", { name: "Request review resume evidence" }),
    );
    expect(
      await screen.findByText(/Mock simulation · MockAIProvider/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/AI-assisted review/)).not.toBeInTheDocument();
  });

  it("shows safe errors and permits explicit retry while preserving consent", async () => {
    const api = fixture(),
      user = userEvent.setup();
    vi.mocked(api.review).mockRejectedValueOnce(
      new Error("The AI provider is rate limited. Saved work is retained."),
    );
    render(
      <AIReview
        api={api}
        resource="defense/run-1/1"
        label="Review defense answer 1"
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Review defense answer 1" }),
    );
    await user.click(await screen.findByRole("checkbox"));
    await user.click(
      screen.getByRole("button", { name: "Request review defense answer 1" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(/rate limited/);
    expect(screen.getByRole("checkbox")).toBeChecked();
    await user.click(
      screen.getByRole("button", { name: "Request review defense answer 1" }),
    );
    expect(await screen.findByText(/AI-assisted review/)).toBeInTheDocument();
    expect(api.review).toHaveBeenCalledTimes(2);
  });

  it("sends only source IDs, consent and provider version using the account request", async () => {
    const request = vi
      .fn<(path: string, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            data: { summary: "Review", suggestions: ["Explain testing"] },
            provenance: {
              provider: "XkiroProvider",
              model: "qwen/qwen3.8-max:free",
              kind: "model_assisted",
              disclosure: "Review required",
            },
          }),
        ),
      );
    const result = await createAIReviewApi(request).review(
      "resumes/id",
      "version",
    );
    expect(result.provider).toBe("XkiroProvider");
    const call = request.mock.calls[0];
    if (!call || !call[1] || typeof call[1].body !== "string")
      throw new Error("Expected one review request with a JSON body.");
    const [path, init] = call;
    expect(path).toBe("/api/v1/account/ai/resumes/id");
    expect(JSON.parse(call[1].body)).toEqual({
      consent: true,
      provider_version: "version",
    });
    expect(JSON.stringify(init)).not.toMatch(/XKIRO_API_KEY|api_key|owner_id/);
    expect(createProjectApi(request, "demo").ai).toBeUndefined();
  });

  it("discloses xKiro and downstream sharing before starting an assessment", () => {
    render(
      <AssessmentConfigure
        options={{
          ...assessmentOptions,
          conceptual_provider: "XkiroProvider",
          conceptual_kind: "model_assisted",
        }}
        busy={false}
        onStart={vi.fn()}
      />,
    );
    expect(
      screen.getByText(/xKiro and its downstream model provider/),
    ).toHaveTextContent(/Third-party retention/);
  });

  it("discloses xKiro rather than claiming no external calls for interviews", async () => {
    const options: InterviewOptions = {
      max_followups: 3,
      answer_limit: 10000,
      notices: [],
      provider: {
        name: "XkiroProvider",
        version: "test",
        model: "qwen/qwen3.8-max:free",
        kind: "model_assisted",
        disclosure: "AI-assisted practice.",
      },
      targets: [],
      inventory: [],
    };
    render(
      <InterviewConfigure options={options} busy={false} onCreate={vi.fn()} />,
    );
    await waitFor(() =>
      expect(
        screen.getByText(
          /Written answers and follow-up context are sent to xKiro/,
        ),
      ).toBeInTheDocument(),
    );
    expect(
      screen.queryByText(/No external AI credentials/),
    ).not.toBeInTheDocument();
  });
});
