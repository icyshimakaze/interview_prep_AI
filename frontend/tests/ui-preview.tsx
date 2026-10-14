import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import type { ReactNode } from "react";

// Actual components rendered with public test fixtures for browser layout/axe QA.
// These ignored artifacts have no React handlers or authentication bypass.
export async function writeUiPreview(
  name: "profile" | "target" | "resume" | "skills",
  content: ReactNode,
) {
  const directory = resolve(process.cwd(), "../.cache/ui-previews");
  await mkdir(directory, { recursive: true });
  await writeFile(
    resolve(directory, `${name}.html`),
    renderToStaticMarkup(
      <main id="main-content" className="mx-auto max-w-5xl px-5 py-8 sm:px-8">
        <p className="eyebrow">
          Static test fixture · layout and accessibility only
        </p>
        {content}
      </main>,
      { identifierPrefix: `${name}-` },
    ),
  );
}
