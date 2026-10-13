"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { checkReadiness, type Readiness } from "@/lib/api/health";

type Status =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "connected"; readiness: Readiness }
  | { state: "error"; message: string };

export function ServiceStatus() {
  const [status, setStatus] = useState<Status>({ state: "idle" });

  async function verify() {
    setStatus({ state: "loading" });
    try {
      setStatus({ state: "connected", readiness: await checkReadiness() });
    } catch (error: unknown) {
      setStatus({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Connection failed. Please try again.",
      });
    }
  }

  return (
    <div className="space-y-5">
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="min-h-16 text-sm leading-6 text-slate-700"
      >
        {status.state === "idle" && (
          <p>
            Check that this frontend can reach the API and its PostgreSQL
            database.
          </p>
        )}
        {status.state === "loading" && <p>Checking the API and database…</p>}
        {status.state === "connected" && (
          <div>
            <p className="font-semibold text-teal-800">
              API connected · PostgreSQL connected
            </p>
            <p>
              Database schema: <code>{status.readiness.schema_revision}</code>
            </p>
          </div>
        )}
        {status.state === "error" && (
          <p className="text-red-800">{status.message}</p>
        )}
      </div>
      <Button
        onClick={() => void verify()}
        disabled={status.state === "loading"}
      >
        {status.state === "loading"
          ? "Checking connection…"
          : status.state === "error"
            ? "Try again"
            : "Verify connection"}
      </Button>
    </div>
  );
}
