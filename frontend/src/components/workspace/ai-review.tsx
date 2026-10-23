"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import type {
  AIReviewApi,
  AIReviewOptions,
  AIReviewResult,
} from "@/lib/api/ai-review";

export function AIReview({
  api,
  resource,
  label,
}: {
  api: AIReviewApi;
  resource: string;
  label: string;
}) {
  const [options, setOptions] = useState<AIReviewOptions | null>(null);
  const [result, setResult] = useState<AIReviewResult | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);
  const consentInput = useRef<HTMLInputElement>(null);
  const resultTitle = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (result) resultTitle.current?.focus();
    else if (options) consentInput.current?.focus();
  }, [options, result]);

  async function act() {
    if (lock.current || (options && !consent)) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      if (!options) setOptions(await api.options());
      else setResult(await api.review(resource, options.version));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Review is unavailable. Saved work is retained.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <div className="mt-5 min-w-0 space-y-3 border-t border-line pt-4 [overflow-wrap:anywhere]">
      {result ? (
        <>
          <p ref={resultTitle} tabIndex={-1} className="text-sm font-semibold">
            {result.kind === "simulation"
              ? "Mock simulation"
              : "AI-assisted review"}{" "}
            · {result.provider}
            {result.model ? ` · ${result.model}` : ""}
          </p>
          <p className="text-sm">{result.disclosure}</p>
          <p className="text-sm whitespace-pre-wrap">{result.summary}</p>
          <ul className="list-disc space-y-2 pl-5 text-sm">
            {result.suggestions.map((suggestion, i) => (
              <li key={i}>{suggestion}</li>
            ))}
          </ul>
          <p className="text-xs text-muted">
            Saved for reuse for up to 30 days. Requires human review; does not
            verify skill or change evidence, requirements, plans or saved
            defenses.
          </p>
        </>
      ) : (
        <>
          {options && (
            <>
              <p className="text-sm">{options.disclosure}</p>
              <label className="flex items-start gap-3 text-sm">
                <input
                  ref={consentInput}
                  type="checkbox"
                  checked={consent}
                  disabled={busy}
                  onChange={(event) => setConsent(event.target.checked)}
                  className="mt-1"
                />
                {options.kind === "simulation"
                  ? `I understand ${label.toLowerCase()} uses deterministic mock simulation.`
                  : `I agree to send this review's data to ${options.name}.`}
              </label>
            </>
          )}
          <Button
            variant="outline"
            disabled={busy || (!!options && !consent)}
            onClick={() => void act()}
          >
            {busy
              ? "Loading review…"
              : options
                ? `Request ${label.toLowerCase()}`
                : label}
          </Button>
          <p className="text-xs text-muted" role="status">
            {busy ? "Please wait; your saved work is retained." : ""}
          </p>
        </>
      )}
      {error && (
        <p className="text-sm text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
