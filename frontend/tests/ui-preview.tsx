import { renderToStaticMarkup } from "react-dom/server";
import type { ReactNode } from "react";

// Layout/accessibility only: these contain no event handlers or authenticated session.
export function renderUiPreview(name: string, content: ReactNode): string {
  return renderToStaticMarkup(
    <main id="main-content" className="mx-auto max-w-5xl px-5 py-8 sm:px-8">
      <p className="eyebrow">
        Static test fixture ? layout and accessibility only
      </p>
      {content}
    </main>,
    { identifierPrefix: `${name}-` },
  );
}
