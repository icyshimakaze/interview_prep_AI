import type { Question } from "@/lib/api/questions";
import { Button } from "@/components/ui/button";
import { Badge, DataTable } from "@/components/ui/table";

export function QuestionResults({
  questions,
  busy,
  onSelect,
  bookmark,
}: {
  questions: Question[];
  busy: boolean;
  onSelect: (id: string) => void;
  bookmark: (question: Question) => Promise<void>;
}) {
  return (
    <DataTable
      caption="Question bank results"
      headers={[
        "Question",
        "Topic / difficulty",
        "Type / relevance",
        "Your practice",
      ]}
    >
      {questions.map((question) => (
        <tr key={question.id}>
          <th scope="row">
            <Button
              variant="ghost"
              onClick={() => onSelect(question.id)}
              className="text-left whitespace-normal"
            >
              {question.title}
            </Button>
            <p className="mt-2 text-xs font-normal text-muted">
              {question.source_classification.replaceAll("_", " ")}
            </p>
          </th>
          <td>
            {question.category}
            <p className="my-2 text-xs text-muted">{question.subtopic}</p>
            <Badge>{question.difficulty}</Badge>
          </td>
          <td>
            {question.question_type.replaceAll("_", " ")}
            <p className="mt-2 max-w-xs text-xs whitespace-normal text-muted">
              {question.roles.join(", ")}
            </p>
            <p className="mt-2 text-xs text-muted">
              {question.tags.join(" · ")}
            </p>
          </td>
          <td>
            <p className="mb-3 text-sm">
              {question.attempted ? "Attempted" : "Not attempted"}
            </p>
            <Button
              variant="outline"
              disabled={busy || (!question.active && !question.bookmarked)}
              aria-pressed={question.bookmarked}
              aria-label={`${question.bookmarked ? "Remove bookmark" : "Bookmark"}: ${question.title}`}
              onClick={() => void bookmark(question)}
            >
              {question.bookmarked ? "Remove bookmark" : "Bookmark"}
            </Button>
          </td>
        </tr>
      ))}
    </DataTable>
  );
}
