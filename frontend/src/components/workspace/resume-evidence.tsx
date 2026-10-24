import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/table";
import { categoryLabels, type Evidence, type Resume } from "@/lib/api/resumes";

export function ResumeEvidence({
  resume,
  busy,
  onEdit,
  onDelete,
}: {
  resume: Resume;
  busy: boolean;
  onEdit: (item: Evidence) => void;
  onDelete: (item: Evidence) => void;
}) {
  return (
    <>
      <div className="mt-5">
        <Badge tone={resume.is_sample ? "amber" : "neutral"}>
          {resume.is_sample
            ? "Fictional sample resume"
            : "Your uploaded resume"}
        </Badge>
      </div>
      <p className="mt-5 max-w-3xl text-sm leading-7 text-muted">
        Extraction finds explicit text mentions, including negative or
        aspirational mentions. Review the excerpt before accepting a claim.
        Missing evidence never means you do not know something.
      </p>
      {resume.extraction_note === "no_text" && (
        <p className="mt-4 border-l-2 border-line pl-4 text-sm leading-7">
          No selectable text was found. This may be a scan. Add your evidence
          manually or upload a PDF exported with selectable text.
        </p>
      )}
      {resume.extraction_note === "evidence_limit" && (
        <p className="mt-4 text-sm leading-7">
          Extraction reached the 100-entry limit. Review these entries and
          remove unwanted ones before adding more.
        </p>
      )}
      {!resume.evidence.length && (
        <div className="mt-6 border-y border-line py-8">
          <h3 className="font-serif text-xl">No evidence detected in resume</h3>
          <p className="mt-3 text-sm leading-7 text-muted">
            This means the extractor did not find supported mentions. It makes
            no judgment about your knowledge or experience. You can add
            information below.
          </p>
        </div>
      )}
      <ul className="mt-6 divide-y border-y border-line">
        {resume.evidence.map((item) => (
          <li key={item.id} className="py-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0 flex-1 basis-64">
                <p className="eyebrow">
                  {categoryLabels[item.category]} ·{" "}
                  {item.origin === "user" ? "Added by you" : "PDF mention"}
                </p>
                <h3 className="mt-3 text-base leading-7 font-semibold break-words whitespace-pre-wrap">
                  {item.user_correction ?? item.claim}
                </h3>
              </div>
              <Badge
                tone={
                  item.review_status === "confirmed"
                    ? "green"
                    : item.review_status === "rejected"
                      ? "neutral"
                      : "amber"
                }
              >
                {item.review_status === "confirmed"
                  ? "Confirmed by you"
                  : item.review_status === "rejected"
                    ? "Rejected"
                    : "Needs review"}
              </Badge>
            </div>
            {item.source_excerpt && (
              <div className="mt-4 border-l-2 border-line pl-4">
                <p className="text-xs text-muted">
                  Source excerpt
                  {item.source_page ? ` · page ${item.source_page}` : ""}
                </p>
                <p className="mt-1 text-sm leading-7 break-words whitespace-pre-wrap text-muted">
                  {item.source_excerpt}
                </p>
              </div>
            )}
            {item.review_status === "rejected" && (
              <p className="mt-3 text-xs text-muted">
                Excluded from preparation context. Kept here for your review
                until deleted.
              </p>
            )}
            <div className="mt-4 flex flex-wrap gap-3">
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => onEdit(item)}
                aria-label={`Review ${item.user_correction ?? item.claim}`}
              >
                Review / correct
              </Button>
              <Button
                variant="ghost"
                disabled={busy}
                onClick={() => onDelete(item)}
                aria-label={`Delete evidence ${item.user_correction ?? item.claim}`}
              >
                Delete entry
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
