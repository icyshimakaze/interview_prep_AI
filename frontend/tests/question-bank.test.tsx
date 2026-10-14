import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QuestionBankView } from "@/components/workspace/question-bank-view";
import { QuestionDetailView } from "@/components/workspace/question-detail";
import {
  createQuestionApi,
  initialQuestionFilters,
  parseQuestionDetail,
  parseQuestionPage,
  type QuestionPage,
} from "@/lib/api/questions";
import {
  questionApiFixture,
  questionFixture,
  questionPageFixture,
} from "./question-fixture";

describe("question bank", () => {
  it("applies search, actual difficulty/type/role/topic filters and resets pagination", async () => {
    const user = userEvent.setup(),
      api = questionApiFixture();
    api.list = vi.fn().mockResolvedValue(questionPageFixture);
    render(<QuestionBankView api={api} mode="account" />);
    await screen.findByRole("button", { name: "Two Sum Problem" });
    await user.click(screen.getByRole("button", { name: "Next page" }));
    await waitFor(() =>
      expect(api.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ offset: 12 }),
        expect.any(AbortSignal),
      ),
    );
    await user.selectOptions(screen.getByLabelText("Difficulty"), "hard");
    await waitFor(() =>
      expect(api.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ difficulty: "hard", offset: 0 }),
        expect.any(AbortSignal),
      ),
    );
    await user.selectOptions(screen.getByLabelText("Question type"), "design");
    await user.selectOptions(
      screen.getByLabelText("Role"),
      "software-engineer",
    );
    await user.selectOptions(screen.getByLabelText("Topic"), "Hash lookup");
    await user.type(screen.getByLabelText("Search questions"), " arrays ");
    await user.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() =>
      expect(api.list).toHaveBeenLastCalledWith(
        expect.objectContaining({
          search: "arrays",
          difficulty: "hard",
          question_type: "design",
          role: "software-engineer",
          subtopic: "Hash lookup",
        }),
        expect.any(AbortSignal),
      ),
    );
  });

  it("filters bookmarks and attempted state and retains a failed bookmark gesture", async () => {
    const user = userEvent.setup(),
      api = questionApiFixture();
    api.bookmark = vi
      .fn()
      .mockRejectedValueOnce(new Error("Network unavailable"))
      .mockResolvedValueOnce(true);
    api.list = vi.fn().mockResolvedValue(questionPageFixture);
    render(<QuestionBankView api={api} mode="account" />);
    await screen.findByRole("button", { name: "Two Sum Problem" });
    await user.click(
      screen.getByRole("button", { name: "Bookmark: Two Sum Problem" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Network unavailable",
    );
    await user.click(
      screen.getByRole("button", { name: "Bookmark: Two Sum Problem" }),
    );
    expect(api.bookmark).toHaveBeenCalledWith("question-one", true);
    await user.selectOptions(screen.getByLabelText("Bookmarks"), "yes");
    await user.selectOptions(screen.getByLabelText("Attempted state"), "no");
    await waitFor(() =>
      expect(api.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ bookmarked: "yes", attempted: "no" }),
        expect.any(AbortSignal),
      ),
    );
  });

  it("ignores a stale page and displays loading and empty states", async () => {
    const user = userEvent.setup(),
      api = questionApiFixture();
    let finish: (value: QuestionPage) => void = () => {
      throw new Error("Not started");
    };
    const older = new Promise<QuestionPage>((resolve) => {
      finish = resolve;
    });
    api.list = vi
      .fn()
      .mockReturnValueOnce(older)
      .mockResolvedValueOnce({ ...questionPageFixture, items: [], total: 0 });
    render(<QuestionBankView api={api} mode="account" />);
    expect(screen.getByText("Loading questions…")).toBeVisible();
    await user.selectOptions(screen.getByLabelText("Difficulty"), "hard");
    await screen.findByText("No questions match this view");
    await act(async () => finish(questionPageFixture));
    expect(
      screen.queryByRole("button", { name: "Two Sum Problem" }),
    ).not.toBeInTheDocument();
  });

  it("withholds concepts, retains failed answers and retries the same submission key", async () => {
    const user = userEvent.setup(),
      api = questionApiFixture();
    api.submit = vi
      .fn()
      .mockRejectedValueOnce(new Error("Submission could not be confirmed"))
      .mockResolvedValueOnce({
        id: "attempt",
        answer_text: "My reasoning",
        question_version_id: "version-two",
        submitted_at: "2026-10-14T00:00:00Z",
        result_kind: "self_review",
      });
    api.read = vi
      .fn()
      .mockResolvedValueOnce(questionFixture)
      .mockResolvedValueOnce({
        ...questionFixture,
        attempted: true,
        concepts_unlocked: true,
        expected_concepts: ["Look up previously visited complements."],
      });
    render(
      <QuestionDetailView
        api={api}
        id="question-one"
        mode="account"
        onBack={() => undefined}
      />,
    );
    await screen.findByText(questionFixture.prompt);
    expect(
      screen.queryByText("Look up previously visited complements."),
    ).not.toBeInTheDocument();
    await user.type(screen.getByLabelText("Your response"), "My reasoning");
    await user.click(
      screen.getByRole("button", { name: "Submit for self-review" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "could not be confirmed",
    );
    expect(screen.getByLabelText("Your response")).toHaveValue("My reasoning");
    await user.click(
      screen.getByRole("button", { name: "Submit for self-review" }),
    );
    expect(
      await screen.findByText("Look up previously visited complements."),
    ).toBeVisible();
    expect(vi.mocked(api.submit).mock.calls[0]?.[1]).toEqual(
      vi.mocked(api.submit).mock.calls[1]?.[1],
    );
    expect(
      screen.getByText(/does not generate an assessment score/),
    ).toBeVisible();
  });

  it("shows submitted history and deletes only question-bank attempts with confirmation", async () => {
    const user = userEvent.setup(),
      api = questionApiFixture();
    api.removeAttempt = vi.fn().mockResolvedValue(undefined);
    api.history = vi
      .fn()
      .mockResolvedValueOnce({
        items: [
          {
            id: "attempt-one",
            question_version_id: "version-two",
            channel: "question_bank",
            submitted_at: "2026-10-14T00:00:00Z",
            response: "Private saved response",
            result_kind: "self_review",
          },
        ],
        total: 1,
        offset: 0,
        limit: 10,
      })
      .mockResolvedValueOnce({ items: [], total: 0, offset: 0, limit: 10 });
    render(
      <QuestionDetailView
        api={api}
        id="question-one"
        mode="account"
        onBack={() => undefined}
      />,
    );
    await screen.findByText("Private saved response");
    await user.click(screen.getByText("Delete this saved practice response"));
    await user.click(screen.getByRole("button", { name: "Delete response" }));
    expect(api.removeAttempt).toHaveBeenCalledWith(
      "question-one",
      "attempt-one",
    );
    expect(await screen.findByText("No submitted attempts yet.")).toBeVisible();
  });

  it("rejects malformed enums, pagination and pre-attempt concept disclosures", () => {
    expect(parseQuestionDetail(questionFixture)).toEqual(questionFixture);
    expect(() =>
      parseQuestionPage({ ...questionPageFixture, limit: 0 }),
    ).toThrow();
    expect(() =>
      parseQuestionDetail({ ...questionFixture, difficulty: "expert" }),
    ).toThrow();
    expect(() =>
      parseQuestionDetail({
        ...questionFixture,
        expected_concepts: ["Leaked answer"],
      }),
    ).toThrow();
  });

  it("sends filters and explicit submit/bookmark mutations through authenticated transport", async () => {
    const request = vi
      .fn()
      .mockImplementation(async () => Response.json(questionPageFixture));
    const api = createQuestionApi(request, "account");
    await api.list({
      ...initialQuestionFilters,
      difficulty: "hard",
      search: "SQL & NULL",
      offset: 12,
    });
    const url = new URL(request.mock.calls[0]?.[0] ?? "", "http://test");
    expect(url.searchParams.get("difficulty")).toBe("hard");
    expect(url.searchParams.get("search")).toBe("SQL & NULL");
    expect(url.searchParams.get("offset")).toBe("12");
    request.mockImplementationOnce(async () =>
      Response.json({ bookmarked: true }),
    );
    await api.bookmark("question-one", true);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/account/questions/question-one/bookmark",
      expect.objectContaining({ method: "PUT", body: "{}" }),
    );
  });
});
