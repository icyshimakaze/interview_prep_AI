"use client";
import { ErrorDisplay } from "@/components/ui/states";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <ErrorDisplay
      title="This section could not load"
      message="Your saved data is unchanged. Try loading this section again."
      onRetry={reset}
    />
  );
}
