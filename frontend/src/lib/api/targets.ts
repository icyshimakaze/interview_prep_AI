import {
  parseTarget,
  parseTargetList,
  type Target,
  type TargetInput,
  type TargetList,
  type TargetStatus,
} from "./workspace";
import { createAIReviewApi, type AIReviewApi } from "./ai-review";

export type TargetApi = {
  ai?: AIReviewApi;
  list: (
    offset: number,
    status: TargetStatus | "all",
    signal?: AbortSignal,
  ) => Promise<TargetList>;
  save: (input: TargetInput, target: Target | null) => Promise<Target>;
  remove: (target: Target) => Promise<void>;
  read: (id: string) => Promise<Target>;
};

export function createTargetApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
): TargetApi {
  return {
    ai: createAIReviewApi(request),
    list: async (offset, status, signal) =>
      parseTargetList(
        await (
          await request(
            `/api/v1/account/targets?limit=20&offset=${offset}${status === "all" ? "" : `&status=${status}`}`,
            { signal },
          )
        ).json(),
      ),
    read: async (id) =>
      parseTarget(
        await (
          await request(`/api/v1/account/targets/${encodeURIComponent(id)}`)
        ).json(),
      ),
    save: async (input, target) =>
      parseTarget(
        await (
          await request(
            target
              ? `/api/v1/account/targets/${encodeURIComponent(target.id)}`
              : "/api/v1/account/targets",
            {
              method: target ? "PUT" : "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(
                target
                  ? { ...input, expected_revision: target.revision }
                  : input,
              ),
            },
          )
        ).json(),
      ),
    remove: async (target) => {
      await request(
        `/api/v1/account/targets/${encodeURIComponent(target.id)}?expected_revision=${target.revision}`,
        { method: "DELETE" },
      );
    },
  };
}
