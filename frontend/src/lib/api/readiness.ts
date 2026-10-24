// Retry only a read-only readiness probe. Workspace mutations are never replayed
// here: a lost response may still have committed on the server.
export async function waitForWorkspace(): Promise<void> {
  const deadline = AbortSignal.timeout(75000);
  while (!deadline.aborted) {
    try {
      const response = await fetch("/api/v1/health/ready", {
        cache: "no-store",
        credentials: "same-origin",
        signal: AbortSignal.any([deadline, AbortSignal.timeout(10000)]),
      });
      if (response.ok) return;
      if (![502, 503, 504].includes(response.status)) break;
    } catch {
      if (deadline.aborted) break;
    }
    await new Promise<void>((resolve) => {
      if (deadline.aborted) return resolve();
      const complete = () => {
        clearTimeout(timer);
        deadline.removeEventListener("abort", complete);
        resolve();
      };
      const timer = setTimeout(complete, 1000);
      deadline.addEventListener("abort", complete, { once: true });
    });
  }
  throw new Error(
    "The practice server is still starting or unavailable. Please try again in a minute.",
  );
}
