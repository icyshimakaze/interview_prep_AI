import type { Target } from "@/lib/api/workspace";
import { Badge } from "@/components/ui/table";

export function TargetDetails({ target }: { target: Target }) {
  return (
    <article className="mt-5 space-y-6">
      <div>
        <h3 className="section-title">{target.title}</h3>
        {target.organization && (
          <p className="mt-2 text-sm text-muted">{target.organization}</p>
        )}
        <div className="mt-4 flex gap-3">
          <Badge>{target.status}</Badge>
          <Badge tone={target.priority === "high" ? "amber" : "neutral"}>
            {target.priority} priority
          </Badge>
        </div>
      </div>
      <section>
        <h3 className="text-sm font-semibold">Job description</h3>
        <p className="mt-3 text-sm leading-7 break-words whitespace-pre-wrap text-muted">
          {target.description ?? "No description recorded."}
        </p>
      </section>
      {target.notes && (
        <section>
          <h3 className="text-sm font-semibold">Your notes</h3>
          <p className="mt-3 text-sm leading-7 break-words whitespace-pre-wrap text-muted">
            {target.notes}
          </p>
        </section>
      )}
      {target.source_url && (
        <a
          href={target.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-link break-all"
        >
          Open source link (new tab)
        </a>
      )}
      <p className="border-t border-line pt-4 text-xs leading-6 text-muted">
        This is supplied job context, not a skills assessment. Description
        changes retain previous versions for preparation history until deletion
        is permitted.
      </p>
    </article>
  );
}
