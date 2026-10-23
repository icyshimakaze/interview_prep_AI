import Link from "next/link";
import type { ReactNode } from "react";
import { Brand } from "@/components/brand";
import { ButtonLink } from "@/components/ui/button";

export function PublicShell({ children }: { children: ReactNode }) {
  return (
    <>
      <header className="border-b border-line">
        <div className="public-width flex min-h-20 flex-wrap items-center justify-between gap-x-6 gap-y-1 py-3">
          <Brand />
          <nav
            aria-label="Main navigation"
            className="order-3 flex w-full gap-6 border-t border-line pt-2 text-sm text-muted sm:order-none sm:w-auto sm:border-0 sm:pt-0"
          >
            <Link
              href="/#product"
              className="inline-flex min-h-11 items-center hover:text-accent"
            >
              Product
            </Link>
            <Link
              href="/#how-it-works"
              className="inline-flex min-h-11 items-center hover:text-accent"
            >
              How it works
            </Link>
            <Link
              href="/privacy"
              className="inline-flex min-h-11 items-center hover:text-accent"
            >
              Privacy
            </Link>
          </nav>
          <ButtonLink href="/sign-in" variant="outline">
            Sign in
          </ButtonLink>
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className="focus:outline-none">
        {children}
      </main>
      <footer className="border-t border-line">
        <div className="public-width grid gap-8 py-12 sm:grid-cols-[1fr_auto]">
          <div>
            <Brand />
            <p className="mt-3 max-w-sm text-sm leading-6 text-muted">
              Job targets, interview practice, and a record of your preparation.
            </p>
          </div>
          <nav
            aria-label="Footer navigation"
            className="flex flex-wrap gap-x-8 gap-y-1 text-sm"
          >
            <Link href="/#features" className="text-link">
              Features
            </Link>
            <Link href="/demo" className="text-link">
              Explore demo
            </Link>
            <Link href="/privacy" className="text-link">
              Privacy & data
            </Link>
            <Link href="/status" className="text-link">
              Service status
            </Link>
          </nav>
          <p className="text-xs leading-6 text-muted sm:col-span-2">
            Interview Prep · Development preview. Sample activity is labeled; no
            interview outcomes are promised.
          </p>
        </div>
      </footer>
    </>
  );
}
