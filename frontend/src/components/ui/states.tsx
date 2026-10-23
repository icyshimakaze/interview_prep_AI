import type { ReactNode } from "react";
import { Button } from "./button";
import { Icon, type IconName } from "./icon";

export function EmptyState({
  icon,
  title,
  description,
  action,
  note,
}: {
  icon: IconName;
  title: string;
  description: string;
  action?: ReactNode;
  note?: string;
}) {
  return (
    <section className="empty-state">
      <span className="empty-icon">
        <Icon name={icon} width={26} height={26} />
      </span>
      <h2 className="section-title">{title}</h2>
      <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-muted">
        {description}
      </p>
      {action && <div className="mt-6">{action}</div>}
      {note && (
        <p className="mx-auto mt-5 max-w-md text-xs leading-6 text-muted">
          {note}
        </p>
      )}
    </section>
  );
}

export function ErrorDisplay({
  title = "Something needs attention",
  message,
  onRetry,
  busy = false,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
  busy?: boolean;
}) {
  return (
    <div className="error-display">
      <div role="alert">
        <h2 className="font-semibold">{title}</h2>
        <p className="mt-1 text-sm leading-6">{message}</p>
      </div>
      {onRetry && (
        <Button
          variant="outline"
          className="mt-4"
          onClick={onRetry}
          disabled={busy}
        >
          {busy ? "Trying again…" : "Try again"}
        </Button>
      )}
    </div>
  );
}

export function WorkspaceSkeleton({
  label = "Loading your preparation workspace…",
}: {
  label?: string;
}) {
  return (
    <div role="status" aria-busy="true" className="space-y-8">
      <p className="text-sm text-muted">{label}</p>
      <div aria-hidden="true" className="space-y-4">
        <div className="skeleton h-4 w-24" />
        <div className="skeleton h-10 w-2/3 max-w-sm" />
        <div className="skeleton h-4 w-4/5 max-w-lg" />
        <div className="my-10 border-t border-line" />
        <div className="skeleton h-36 w-full" />
        <div className="skeleton h-16 w-full" />
        <div className="skeleton h-16 w-full" />
      </div>
    </div>
  );
}
