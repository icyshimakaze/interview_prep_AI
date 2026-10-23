export type AIReviewOptions = {
  name: string;
  version: string;
  kind: "simulation" | "model_assisted";
  disclosure: string;
};
export type AIReviewResult = {
  summary: string;
  suggestions: string[];
  provider: string;
  model: string | null;
  kind: "simulation" | "model_assisted";
  disclosure: string;
};
export type AIReviewApi = ReturnType<typeof createAIReviewApi>;

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("The AI review response is invalid.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string" || !value.trim())
    throw new Error("The AI review response is invalid.");
  return value;
}
function kind(value: unknown): AIReviewOptions["kind"] {
  if (value !== "simulation" && value !== "model_assisted")
    throw new Error("The AI review provenance is invalid.");
  return value;
}
export function createAIReviewApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
) {
  const root = "/api/v1/account/ai";
  return {
    options: async (): Promise<AIReviewOptions> => {
      const row = object(await (await request(`${root}/options`)).json());
      return {
        name: text(row.name),
        version: text(row.version),
        kind: kind(row.kind),
        disclosure: text(row.disclosure),
      };
    },
    review: async (
      resource: string,
      providerVersion: string,
    ): Promise<AIReviewResult> => {
      const response = await request(`${root}/${resource}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: AbortSignal.timeout(75000),
        body: JSON.stringify({
          consent: true,
          provider_version: providerVersion,
        }),
      });
      const row = object(await response.json());
      const data = object(row.data),
        provenance = object(row.provenance);
      let suggestions: unknown =
        data.suggestions ?? data.improvements ?? data.review_notes;
      let summary: unknown = data.summary ?? data.overall_feedback;
      if (Array.isArray(data.questions)) {
        summary =
          "Generated practice questions from static facts; your saved defense is unchanged.";
        suggestions = data.questions.map((value: unknown) => {
          const item = object(value);
          return `${text(item.focus)}: ${text(item.question)} Evidence: ${text(item.evidence)}`;
        });
      } else if (Array.isArray(data.steps)) {
        suggestions = data.steps.map((value: unknown) => {
          const item = object(value);
          if (
            typeof item.minutes !== "number" ||
            !Number.isInteger(item.minutes) ||
            item.minutes < 1
          )
            throw new Error("Invalid review duration.");
          return `${text(item.topic)} (${item.minutes} minutes): ${text(item.activity)} Check: ${text(item.success_check)}`;
        });
      }
      if (!Array.isArray(suggestions))
        throw new Error("Invalid review suggestions.");
      const notes = suggestions.map(text);
      const mentions: unknown = data.requirements ?? data.skills;
      if (Array.isArray(mentions)) {
        notes.push(
          ...mentions.map((value: unknown) => {
            const item = object(value);
            return `${text(item.name)}${item.importance ? ` (${text(item.importance)})` : ""}: ${text(item.evidence)}`;
          }),
        );
      }
      return {
        summary: text(summary),
        suggestions: notes,
        provider: text(provenance.provider),
        model: provenance.model === null ? null : text(provenance.model),
        kind: kind(provenance.kind),
        disclosure: text(provenance.disclosure),
      };
    },
  };
}
