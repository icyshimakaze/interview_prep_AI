import type { Project } from "@/lib/api/projects";

function Facts({ facts }: { facts: Project["facts"] }) {
  return facts.length ? (
    <ul className="divide-y divide-line border-y border-line">
      {facts.map((f, i) => (
        <li key={i} className="py-3">
          <strong>
            {f.inferred ? "Inferred" : "Observed"} · {f.kind}
          </strong>
          <p>{f.description}</p>
          <p className="text-sm break-all">
            {f.path}:{f.line}
          </p>
        </li>
      ))}
    </ul>
  ) : (
    <p>
      No matching static evidence in the inspected files. This does not
      establish absence.
    </p>
  );
}
export function ProjectAnalysis({ project }: { project: Project }) {
  return (
    <div className="space-y-6 text-sm leading-7">
      <h2 className="section-title">Repository analysis</h2>
      <p>
        {project.example
          ? "Illustrative demo fixture"
          : "Imported source snapshot"}{" "}
        · {project.analysis_version}
      </p>
      {project.github_url && (
        <p className="break-all">
          {project.github_url} · Commit {project.commit_sha}
        </p>
      )}
      <ul className="list-disc pl-5">
        {project.summary.notes.map((n) => (
          <li key={n}>{n}</li>
        ))}
      </ul>
      <p>
        {project.files.length} inspected files · {project.summary.skipped_files}{" "}
        skipped files.
        {project.summary.truncated && " Report truncated at analysis limits."}
      </p>
      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Architecture summary</h3>
        <p>
          Probable components and boundaries require your confirmation. A
          dependency or declaration does not prove runtime behavior.
        </p>
        <Facts
          facts={project.facts.filter((f) =>
            [
              "component",
              "database",
              "authentication",
              "route",
              "schema",
            ].includes(f.kind),
          )}
        />
      </section>
      <details className="border-t border-line pt-4">
        <summary className="cursor-pointer font-semibold">
          Technology view
        </summary>
        <p className="my-3">
          Languages by inspected file count:{" "}
          {Object.entries(project.summary.languages)
            .map(([name, count]) => `${name} (${count})`)
            .join(", ") || "Not identified"}
        </p>
        <Facts
          facts={project.facts.filter((f) =>
            ["manifest", "framework", "dependency"].includes(f.kind),
          )}
        />
      </details>
      <details className="border-t border-line pt-4">
        <summary className="cursor-pointer font-semibold">
          Tests, CI, Docker and documentation
        </summary>
        <Facts
          facts={project.facts.filter((f) =>
            ["tests", "ci", "docker", "documentation"].includes(f.kind),
          )}
        />
      </details>
      <details className="border-t border-line pt-4">
        <summary className="cursor-pointer font-semibold">
          Directory structure and inspected files
        </summary>
        <p className="my-3">
          Archive-relative paths are preserved, including any wrapper directory.
          Source contents are not retained.
        </p>
        <ul className="space-y-1 font-mono text-sm">
          {project.files.map((f) => (
            <li className="break-all" key={f.path}>
              {f.path} · {f.line_count} lines · {f.byte_count} bytes
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
