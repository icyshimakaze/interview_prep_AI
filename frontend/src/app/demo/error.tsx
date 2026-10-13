"use client";
import { ErrorDisplay } from "@/components/ui/states";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <ErrorDisplay
      title="This demo section could not load"
      message="Try loading this section again. Your demo remains available until it expires."
      onRetry={reset}
    />
  );
}
