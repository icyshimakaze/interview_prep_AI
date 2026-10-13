import type { components } from "./generated";

export type Readiness = components["schemas"]["ReadinessResponse"];

function isReadiness(value: unknown): value is Readiness {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    value.status === "ok" &&
    "service" in value &&
    value.service === "interview-prep-api" &&
    "database" in value &&
    value.database === "connected" &&
    "schema_revision" in value &&
    typeof value.schema_revision === "string"
  );
}

export async function checkReadiness(): Promise<Readiness> {
  const response = await fetch("/api/v1/health/ready", {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok)
    throw new Error(
      "The API or database is not ready. Start the services and try again.",
    );
  const body: unknown = await response.json();
  if (!isReadiness(body))
    throw new Error("The API returned an unexpected health response.");
  return body;
}
