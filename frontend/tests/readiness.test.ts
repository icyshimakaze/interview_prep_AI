import { afterEach, describe, expect, it, vi } from "vitest";
import { waitForWorkspace } from "@/lib/api/readiness";
import { enterDemo, workspaceRequest } from "@/lib/api/workspace";
import { workspaceFixture } from "./workspace-fixture";

afterEach(() => vi.useRealTimers());

describe("hosted startup and network failures", () => {
  it("waits through a sleeping host before creating exactly one workspace", async () => {
    vi.useFakeTimers();
    let probes = 0;
    const requests: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (path: string, init: RequestInit) => {
        requests.push(path);
        if (path.endsWith("/health/ready")) {
          expect(init.method).toBeUndefined();
          return Response.json({}, { status: ++probes < 3 ? 502 : 200 });
        }
        if (path.endsWith("/sessions")) return Response.json({});
        if (path.endsWith("/dashboard")) return Response.json(workspaceFixture);
        throw new Error("Unexpected request");
      }),
    );
    const result = enterDemo();
    await vi.advanceTimersByTimeAsync(2000);
    expect(await result).toEqual(workspaceFixture);
    expect(requests).toEqual([
      "/api/v1/health/ready",
      "/api/v1/health/ready",
      "/api/v1/health/ready",
      "/api/v1/demo/sessions",
      "/api/v1/demo/dashboard",
    ]);
  });

  it("bounds an unavailable host and never creates a workspace", async () => {
    vi.useFakeTimers();
    vi.spyOn(AbortSignal, "timeout").mockImplementation((duration) => {
      const controller = new AbortController();
      setTimeout(
        () => controller.abort(new DOMException("timeout", "TimeoutError")),
        duration,
      );
      return controller.signal;
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json({}, { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);
    const result = expect(waitForWorkspace()).rejects.toThrow(
      "still starting or unavailable",
    );
    await vi.advanceTimersByTimeAsync(75000);
    await result;
    expect(fetchMock).toHaveBeenCalledTimes(75);
    expect(
      fetchMock.mock.calls.every(([path]) => path === "/api/v1/health/ready"),
    ).toBe(true);
  });

  it("does not repeat mutations after a timeout and shows recovery guidance", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValue(new DOMException("signal timed out", "TimeoutError"));
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      workspaceRequest("/api/v1/demo/interviews", { method: "POST" }),
    ).rejects.toMatchObject({
      code: "request_timeout",
      message: expect.stringContaining("may have been saved"),
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("preserves caller cancellation and hides raw network exception details", async () => {
    const controller = new AbortController();
    controller.abort();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(controller.signal.reason));
    await expect(
      workspaceRequest("/api/v1/demo/interviews", {
        signal: controller.signal,
      }),
    ).rejects.toBe(controller.signal.reason);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("private transport details")),
    );
    await expect(
      workspaceRequest("/api/v1/demo/dashboard"),
    ).rejects.toMatchObject({
      code: "network_unavailable",
      message: expect.not.stringContaining("private"),
    });
  });
});
