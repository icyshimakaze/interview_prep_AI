"use client";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import type {
  Defense,
  Project,
  ProjectApi,
  ProjectSummary,
} from "@/lib/api/projects";
import { ProjectAnalysis } from "./project-analysis";
import { ProjectDefense } from "./project-defense";

export function ProjectsWorkspace({ api }: { api: ProjectApi }) {
  const [items, setItems] = useState<ProjectSummary[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [history, setHistory] = useState<Defense[]>([]);
  const [run, setRun] = useState<Defense | null>(null);
  const [url, setUrl] = useState(""),
    [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const lock = useRef(false),
    startKey = useRef<string | null>(null);
  useEffect(() => {
    let active = true;
    void api
      .list()
      .then((r) => {
        if (active) setItems(r);
      })
      .catch((e: unknown) => {
        if (active)
          setError(e instanceof Error ? e.message : "Projects could not load.");
      });
    return () => {
      active = false;
    };
  }, [api, refresh]);
  async function perform(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The request failed.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function select(p: Project) {
    const h = await api.history(p.id);
    setProject(p);
    setHistory(h);
    startKey.current = null;
    setRefresh((v) => v + 1);
  }
  if (run)
    return (
      <ProjectDefense
        key={run.id}
        initial={run}
        api={api}
        onBack={() => {
          setRun(null);
          if (project)
            void perform(async () => {
              setHistory(await api.history(project.id));
            });
        }}
      />
    );
  return (
    <div className="space-y-6">
      <h1 className="page-title">Project Repository</h1>
      <p>
        Prepare to defend a project you built. Import public GitHub source or a
        ZIP, inspect static evidence, then practice explaining decisions and
        AI-assisted work.
      </p>
      <p className="text-sm">
        No repository code, package scripts, tests or containers are run.
        Archives and source contents are discarded after analysis. Paths, facts
        and your answers are saved. Up to five snapshots and twenty practice
        sessions per snapshot.
      </p>
      {error && <p role="alert">{error}</p>}
      {busy && <p role="status">Working on your project…</p>}
      <section className="space-y-4 rounded-xl border p-5">
        <h2 className="text-xl font-semibold">Add a project</h2>
        <form
          className="flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            void perform(async () => select(await api.github(url.trim())));
          }}
        >
          <label className="flex-1">
            Public GitHub repository URL
            <input
              className="mt-1 w-full rounded-lg border p-2"
              type="url"
              required
              maxLength={250}
              placeholder="https://github.com/owner/repository"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </label>
          <Button disabled={busy} type="submit">
            Analyze GitHub repository
          </Button>
        </form>
        <form
          className="flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (file)
              void perform(async () => {
                if (file.size > 10 * 1024 * 1024)
                  throw new Error("Choose a ZIP no larger than 10 MiB.");
                await select(await api.upload(file));
              });
          }}
        >
          <label>
            Source ZIP (10 MiB maximum)
            <input
              className="mt-1 block"
              type="file"
              accept=".zip,application/zip"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <Button disabled={busy || !file} type="submit">
            Analyze ZIP
          </Button>
        </form>
        <Button
          disabled={busy}
          onClick={() => void perform(async () => select(await api.example()))}
        >
          Load illustrative demo project
        </Button>
        <p className="text-sm">
          The demo is an authored teaching fixture analyzed locally, with no
          GitHub or AI service required. Remove secrets before uploading; file
          exclusions are not a comprehensive secret scanner.
        </p>
      </section>
      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Saved repositories</h2>
        {!items.length && <p>No saved project snapshots yet.</p>}
        {items.map((p) => (
          <div
            key={p.id}
            className="flex flex-wrap items-center gap-3 rounded-lg border p-3"
          >
            <Button
              disabled={busy}
              onClick={() =>
                void perform(async () => select(await api.read(p.id)))
              }
            >
              {p.name}
            </Button>
            <span>
              {p.example ? "Demo fixture" : p.origin} ·{" "}
              {new Date(p.created_at).toLocaleString()}
            </span>
            <Button
              disabled={busy}
              onClick={() => {
                if (
                  window.confirm(
                    "Delete this snapshot and all its defense questions and answers?",
                  )
                )
                  void perform(async () => {
                    await api.remove(p.id);
                    if (project?.id === p.id) {
                      setProject(null);
                      setHistory([]);
                    }
                    setRefresh((v) => v + 1);
                  });
              }}
            >
              Delete snapshot
            </Button>
          </div>
        ))}
      </section>
      {project && (
        <>
          <ProjectAnalysis project={project} />
          <section className="space-y-3 rounded-xl border p-5">
            <h2 className="text-xl font-semibold">
              Project Defense interview mode
            </h2>
            <p>
              Ten deterministic questions grounded in this snapshot. Saved
              answers support reflection; this practice does not score
              competence or verify authorship.
            </p>
            <Button
              disabled={busy}
              onClick={() =>
                void perform(async () => {
                  startKey.current ??= crypto.randomUUID();
                  setRun(await api.start(project.id, startKey.current));
                  startKey.current = null;
                })
              }
            >
              Start project defense
            </Button>
            <h3 className="font-semibold">Question history</h3>
            {!history.length && <p>No defense sessions yet.</p>}
            {history.map((h) => (
              <div key={h.id}>
                <Button
                  disabled={busy}
                  onClick={() =>
                    void perform(async () => setRun(await api.readRun(h.id)))
                  }
                >
                  {h.status === "completed" ? "Review" : "Open"} practice ·{" "}
                  {new Date(h.created_at).toLocaleString()}
                </Button>{" "}
                <span>{h.status}</span>
              </div>
            ))}
          </section>
        </>
      )}
    </div>
  );
}
