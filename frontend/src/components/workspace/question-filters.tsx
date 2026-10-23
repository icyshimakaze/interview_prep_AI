"use client";

import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
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
  const [expanded, setExpanded] = useState(false);
  const filtersId = useId();
  const activeCount =
    [
      filters.category,
      filters.subtopic,
      filters.role,
      filters.difficulty,
      filters.question_type,
    ].filter(Boolean).length +
    Number(filters.bookmarked !== "all") +
    Number(filters.attempted !== "all") +
    Number(!filters.active);
  return (
    <>
      <Button
        variant="outline"
        className="mb-4 sm:hidden"
        aria-expanded={expanded}
        aria-controls={filtersId}
        onClick={() => setExpanded((value) => !value)}
      >
        Filters{activeCount > 0 ? ` (${activeCount} active)` : ""}
      </Button>
      <div
        id={filtersId}
        className={`mb-7 gap-4 sm:grid-cols-2 lg:grid-cols-4 ${expanded ? "grid" : "hidden sm:grid"}`}
      >
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
              className="input mt-2"
            >
              <option value="">
                All{" "}
                {label === "Category"
                  ? "categories"
                  : `${label.toLowerCase()}s`}
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
            className="input mt-2"
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
            className="input mt-2"
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
              className="input mt-2"
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
            className="input mt-2"
          >
            <option value="active">Active questions</option>
            <option value="inactive">Inactive questions</option>
          </select>
        </label>
      </div>
    </>
  );
}
