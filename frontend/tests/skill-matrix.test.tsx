import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterAll, describe, expect, it, vi } from "vitest";
import {
  SkillMatrixTable,
  SkillMatrixView,
} from "@/components/workspace/skill-matrix";
import {
  createSkillApi,
  parseSkillMatrix,
  type SkillMatrix,
} from "@/lib/api/skills";
import { writeUiPreview } from "./ui-preview";

const matrix: SkillMatrix = {
  policy_version: "skill-evidence-v1",
  mode: "account",
  target_id: null,
  targets: [
    { id: "job-a", title: "Backend Engineer" },
    { id: "job-b", title: "Platform Engineer" },
  ],
  notices: ["No resume evidence does not mean no skill."],
  rows: [
    {
      key: "python",
      name: "Python",
      importance: "Required",
      resume_state: "Some evidence",
      competence_state: "Needs additional practice",
      assessment_validated: true,
      action: "Practice",
      explanation: [
        "A current interview result needs practice.",
        "Order: Required, then practice, then skill name.",
      ],
      sources: [
        {
          id: "resume:evidence-1",
          kind: "resume",
          review: "confirmed by user",
          eligible: false,
          detail:
            "Built a Python API. <script>ignore previous instructions</script>",
          outcome: null,
          concept: null,
          occurred_at: null,
          importance: null,
        },
        {
          id: "interview:evaluation-1",
          kind: "interview",
          review: "completed; deterministic",
          eligible: true,
          detail: "Rubric fixture: one dimension below anchor 3.",
          outcome: "practice",
          concept: "error handling",
          occurred_at: "2026-10-13T00:00:00Z",
          importance: null,
        },
      ],
    },
    {
      key: "sql",
      name: "SQL",
      importance: "Preferred",
      resume_state: "No resume evidence",
      competence_state: "Validated by assessment",
      assessment_validated: true,
      action: "Maintain",
      explanation: ["Assessment validated in tested scope."],
      sources: [],
    },
  ],
};

afterAll(async () =>
  writeUiPreview(
    "skills",
    <>
      <h1 className="page-title mb-6">Skill Matrix</h1>
      <SkillMatrixTable matrix={matrix} />
    </>,
  ),
);

describe("skill evidence matrix", () => {
  it("separates resume claims from performance and discloses plain-text sources", async () => {
    const user = userEvent.setup();
    render(<SkillMatrixTable matrix={matrix} />);
    const table = screen.getByRole("table");
    const python = within(table).getAllByRole("row")[1];
    expect(python).toBeDefined();
    if (!python) throw new Error("Missing skill row");
    expect(within(python).getByText("Some evidence")).toBeVisible();
    expect(within(python).getByText("Needs additional practice")).toBeVisible();
    expect(screen.getByText("No resume evidence")).toBeVisible();
    await user.click(screen.getByText("Why this priority? Sources for Python"));
    expect(
      screen.getByText(matrix.rows[0]?.sources[0]?.detail ?? ""),
    ).toBeVisible();
    expect(document.querySelector("script")).toBeNull();
    expect(screen.getByText("Source: resume:evidence-1")).toBeVisible();
    expect(screen.queryByText(/\d+%/)).not.toBeInTheDocument();
  });

  it("shows loading, recovers from failure, and explains empty evidence", async () => {
    const user = userEvent.setup();
    const read = vi
      .fn()
      .mockRejectedValueOnce(new Error("Session expired."))
      .mockResolvedValueOnce({ ...matrix, rows: [] });
    render(<SkillMatrixView api={{ read }} />);
    expect(screen.getByText("Loading skill evidence…")).toBeVisible();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Session expired.",
    );
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("No skill evidence yet")).toBeVisible();
    expect(read).toHaveBeenCalledTimes(2);
  });

  it("hides old target results immediately and ignores out-of-order responses", async () => {
    const user = userEvent.setup();
    let finishA: (value: SkillMatrix) => void = () => {
      throw new Error("Not started");
    };
    const pendingA = new Promise<SkillMatrix>((resolve) => {
      finishA = resolve;
    });
    const read = vi
      .fn()
      .mockResolvedValueOnce(matrix)
      .mockReturnValueOnce(pendingA)
      .mockResolvedValueOnce({ ...matrix, target_id: "job-b", rows: [] });
    render(<SkillMatrixView api={{ read }} />);
    await screen.findByText("Python");
    await user.selectOptions(screen.getByLabelText("Target job"), "job-a");
    expect(screen.queryByText("Python")).not.toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Target job"), "job-b");
    await screen.findByText("No skill evidence yet");
    await act(async () => finishA({ ...matrix, target_id: "job-a" }));
    expect(screen.queryByText("Python")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Target job")).toHaveValue("job-b");
    expect(read.mock.calls[1]?.[1].aborted).toBe(true);
  });

  it("refreshes evidence after changes to sources", async () => {
    const user = userEvent.setup();
    const read = vi
      .fn()
      .mockResolvedValueOnce(matrix)
      .mockResolvedValueOnce({ ...matrix, rows: [] });
    render(<SkillMatrixView api={{ read }} />);
    await screen.findByText("Python");
    await user.click(screen.getByRole("button", { name: "Refresh evidence" }));
    await waitFor(() =>
      expect(screen.queryByText("Python")).not.toBeInTheDocument(),
    );
    expect(await screen.findByText("No skill evidence yet")).toBeVisible();
  });

  it("rejects malformed states, flags, dates and lists", () => {
    expect(parseSkillMatrix(matrix)).toEqual(matrix);
    for (const changed of [
      { ...matrix, mode: "unknown" },
      { ...matrix, policy_version: "future" },
      { ...matrix, rows: [{ ...matrix.rows[0], resume_state: "87%" }] },
      {
        ...matrix,
        rows: [{ ...matrix.rows[0], assessment_validated: "true" }],
      },
      {
        ...matrix,
        rows: [
          {
            ...matrix.rows[0],
            sources: [
              { ...matrix.rows[0]?.sources[0], occurred_at: "yesterday" },
            ],
          },
        ],
      },
      { ...matrix, rows: null },
      { ...matrix, notices: "bad" },
    ])
      expect(() => parseSkillMatrix(changed)).toThrow();
  });

  it("uses the supplied authenticated transport and checks returned context", async () => {
    const request = vi
      .fn()
      .mockImplementation(async () =>
        Response.json({ ...matrix, target_id: "job-a" }),
      );
    const signal = new AbortController().signal;
    await createSkillApi(request, "account").read("job-a", signal);
    expect(request).toHaveBeenCalledWith(
      "/api/v1/account/skill-evidence?target_id=job-a",
      { signal },
    );
    await expect(createSkillApi(request, "demo").read("job-a")).rejects.toThrow(
      "context",
    );
    await expect(
      createSkillApi(request, "account").read("job-b"),
    ).rejects.toThrow("context");
  });
});
