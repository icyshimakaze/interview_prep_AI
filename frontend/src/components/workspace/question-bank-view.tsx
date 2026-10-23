"use client";

import { useEffect, useRef, useState } from "react";
import type {
  Question,
  QuestionApi,
  QuestionFacets,
  QuestionFilters,
  QuestionPage,
} from "@/lib/api/questions";
import { initialQuestionFilters } from "@/lib/api/questions";
import { Button } from "@/components/ui/button";
import {
  EmptyState,
  ErrorDisplay,
  WorkspaceSkeleton,
} from "@/components/ui/states";
import { QuestionFiltersView } from "./question-filters";
import { QuestionResults } from "./question-results";
import { SectionHeader } from "./section-header";
import { QuestionDetailView } from "./question-detail";

export function QuestionBankView({
  api,
  mode,
}: {
  api: QuestionApi;
  mode: "account" | "demo";
}) {
  const [filters, setFilters] = useState(initialQuestionFilters);
  const [search, setSearch] = useState("");
  const [facets, setFacets] = useState<QuestionFacets>({
    categories: [],
    subtopics: [],
    roles: [],
  });
  const [refresh, setRefresh] = useState(0);
  const [state, setState] = useState<{
    filters: QuestionFilters;
    refresh: number;
    data?: QuestionPage;
    error?: string;
  } | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const locked = useRef(false);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    void Promise.all([
      api.list(filters, controller.signal),
      api.facets(controller.signal),
    ])
      .then(([data, choices]) => {
        if (active) {
          setState({ filters, refresh, data });
          setFacets(choices);
        }
      })
      .catch((reason: unknown) => {
        if (active)
          setState({
            filters,
            refresh,
            error:
              reason instanceof Error
                ? reason.message
                : "Question bank could not load.",
          });
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, filters, refresh]);
  const current =
    state?.filters === filters && state.refresh === refresh ? state : null;
  const data = current?.data;
  function update(patch: Partial<QuestionFilters>) {
    setFilters((value) => ({ ...value, ...patch, offset: 0 }));
  }
  async function bookmark(question: Question) {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setError(null);
    try {
      await api.bookmark(question.id, !question.bookmarked);
      setRefresh((value) => value + 1);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Bookmark could not be saved.",
      );
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  return (
    <>
      <SectionHeader
        title="Question Bank"
        eyebrow="Focused practice"
        description="Find a reviewed prompt, write your response, and then review the expected concepts."
      />
      {selected ? (
        <QuestionDetailView
          key={selected}
          api={api}
          id={selected}
          mode={mode}
          onBack={() => {
            setSelected(null);
            setRefresh((value) => value + 1);
          }}
        />
      ) : (
        <>
          <form
            className="mb-6 flex flex-wrap items-end gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              update({ search: search.trim() });
            }}
          >
            <label className="min-w-0 flex-1 basis-full text-sm font-medium sm:basis-0">
              Search questions
              <input
                type="search"
                value={search}
                maxLength={100}
                onChange={(event) => setSearch(event.target.value)}
                className="input mt-2"
              />
            </label>
            <Button type="submit">Search</Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSearch("");
                setFilters({ ...initialQuestionFilters });
              }}
            >
              Clear filters
            </Button>
          </form>
          <QuestionFiltersView
            filters={filters}
            facets={facets}
            update={update}
          />
          {error && <ErrorDisplay message={error} />}
          {!current && <WorkspaceSkeleton label="Loading questions…" />}
          {current?.error && (
            <ErrorDisplay
              message={current.error}
              onRetry={() => setRefresh((value) => value + 1)}
            />
          )}
          {data && (
            <>
              <p role="status" className="mb-4 text-sm text-muted">
                {data.total} matching questions · page{" "}
                {Math.floor(data.offset / data.limit) + 1}
              </p>
              {!data.items.length ? (
                <EmptyState
                  icon="questions"
                  title="No questions match this view"
                  description="Adjust your search or filters. Unpublished drafts are excluded."
                />
              ) : (
                <QuestionResults
                  questions={data.items}
                  busy={busy}
                  onSelect={setSelected}
                  bookmark={bookmark}
                />
              )}
              <div className="mt-6 flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  disabled={filters.offset === 0}
                  onClick={() =>
                    setFilters((value) => ({
                      ...value,
                      offset: Math.max(0, value.offset - data.limit),
                    }))
                  }
                >
                  Previous page
                </Button>
                <Button
                  variant="outline"
                  disabled={data.offset + data.limit >= data.total}
                  onClick={() =>
                    setFilters((value) => ({
                      ...value,
                      offset: value.offset + data.limit,
                    }))
                  }
                >
                  Next page
                </Button>
              </div>
            </>
          )}
        </>
      )}
    </>
  );
}
