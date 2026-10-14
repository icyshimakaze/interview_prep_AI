import type {
  Question,
  QuestionFacets,
  QuestionFilters,
} from "@/lib/api/questions";

const types: Question["question_type"][] = [
  "multiple_choice",
  "multiple_select",
  "short_answer",
  "written",
  "design",
  "behavioral",
];
const difficulties: Question["difficulty"][] = ["easy", "medium", "hard"];

export function QuestionFiltersView({
  filters,
  facets,
  update,
}: {
  filters: QuestionFilters;
  facets: QuestionFacets;
  update: (patch: Partial<QuestionFilters>) => void;
}) {
  return (
    <div className="mb-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {(
        [
          ["category", "Category", facets.categories],
          ["subtopic", "Topic", facets.subtopics],
          ["role", "Role", facets.roles],
        ] as const
      ).map(([key, label, options]) => (
        <label key={key} className="min-w-0 text-sm font-medium">
          {label}
          <select
            value={filters[key]}
            onChange={(event) => update({ [key]: event.target.value })}
            className="mt-2 w-full rounded border border-line bg-surface p-3"
          >
            <option value="">
              All{" "}
              {label === "Category" ? "categories" : `${label.toLowerCase()}s`}
            </option>
            {options.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      ))}
      <label className="text-sm font-medium">
        Difficulty
        <select
          value={filters.difficulty}
          onChange={(event) =>
            update({
              difficulty:
                difficulties.find((value) => value === event.target.value) ??
                "",
            })
          }
          className="mt-2 w-full rounded border border-line bg-surface p-3"
        >
          <option value="">All difficulties</option>
          {difficulties.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>
      <label className="text-sm font-medium">
        Question type
        <select
          value={filters.question_type}
          onChange={(event) =>
            update({
              question_type:
                types.find((value) => value === event.target.value) ?? "",
            })
          }
          className="mt-2 w-full rounded border border-line bg-surface p-3"
        >
          <option value="">All types</option>
          {types.map((value) => (
            <option key={value} value={value}>
              {value.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
      {(
        [
          ["bookmarked", "Bookmarks"],
          ["attempted", "Attempted state"],
        ] as const
      ).map(([key, label]) => (
        <label key={key} className="text-sm font-medium">
          {label}
          <select
            value={filters[key]}
            onChange={(event) =>
              update({
                [key]:
                  event.target.value === "yes"
                    ? "yes"
                    : event.target.value === "no"
                      ? "no"
                      : "all",
              })
            }
            className="mt-2 w-full rounded border border-line bg-surface p-3"
          >
            <option value="all">All questions</option>
            <option value="yes">
              {key === "bookmarked" ? "Bookmarked" : "Attempted"}
            </option>
            <option value="no">
              {key === "bookmarked" ? "Not bookmarked" : "Not attempted"}
            </option>
          </select>
        </label>
      ))}
      <label className="text-sm font-medium">
        Active status
        <select
          value={filters.active ? "active" : "inactive"}
          onChange={(event) =>
            update({ active: event.target.value === "active" })
          }
          className="mt-2 w-full rounded border border-line bg-surface p-3"
        >
          <option value="active">Active questions</option>
          <option value="inactive">Inactive questions</option>
        </select>
      </label>
    </div>
  );
}
