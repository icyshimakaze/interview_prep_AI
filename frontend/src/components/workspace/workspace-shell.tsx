"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Brand } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Dialog } from "@/components/ui/dialog";
import { sectionHref, workspaceSections } from "./navigation";

function WorkspaceNav({
  mode,
  pathname,
  onNavigate,
}: {
  mode: "account" | "demo";
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <nav aria-label="Workspace navigation" className="space-y-4">
      {["Workspace", "Prepare", "Practice", "Reflect", "Account"].map(
        (group) => (
          <div key={group}>
            {group !== "Workspace" && (
              <p className="mb-1 px-3 text-[10px] font-semibold tracking-[0.13em] text-muted uppercase">
                {group}
              </p>
            )}
            <ul className="space-y-0.5">
              {workspaceSections
                .filter((section) => section.group === group)
                .map((section) => {
                  const href = sectionHref(mode, section.slug);
                  return (
                    <li key={section.slug}>
                      <Link
                        href={href}
                        aria-current={pathname === href ? "page" : undefined}
                        onClick={onNavigate}
                        className="nav-link"
                      >
                        <Icon name={section.icon} className="shrink-0" />
                        {section.label}
                      </Link>
                    </li>
                  );
                })}
            </ul>
          </div>
        ),
      )}
    </nav>
  );
}

export function WorkspaceShell({
  mode,
  children,
  onLeave,
  busy = false,
}: {
  mode: "account" | "demo";
  children: ReactNode;
  onLeave?: () => void;
  busy?: boolean;
}) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const main = useRef<HTMLElement>(null);
  const previousPath = useRef(pathname);
  useEffect(() => {
    if (previousPath.current !== pathname) main.current?.focus();
    previousPath.current = pathname;
  }, [pathname]);
  const current =
    workspaceSections.find(
      (section) => sectionHref(mode, section.slug) === pathname,
    )?.label ?? "Workspace";
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="sticky top-0 hidden h-screen flex-col overflow-y-auto border-r border-line bg-surface px-4 py-5 lg:flex">
        <div className="mb-7 px-3">
          <Brand />
        </div>
        <WorkspaceNav mode={mode} pathname={pathname} />
        <div className="mt-auto px-3 pt-8">
          <p className="text-xs font-medium">
            {mode === "demo" ? "Demo workspace" : "Your workspace"}
          </p>
          <p className="mt-2 text-xs leading-5 text-muted">
            {mode === "demo"
              ? "Fictional data. A real look around."
              : "Make room for focused preparation."}
          </p>
          <Link href="/privacy" className="text-link mt-2 text-xs">
            Privacy & data
          </Link>
        </div>
      </aside>
      <div className="min-w-0">
        <header className="flex min-h-18 items-center justify-between gap-3 border-b border-line bg-surface px-5 sm:px-8 lg:px-10">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              variant="ghost"
              className="px-2 lg:hidden"
              aria-label="Open navigation"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen(true)}
            >
              <Icon name="menu" />
            </Button>
            <span className="hidden text-sm text-muted sm:inline">
              {mode === "demo" ? "Interactive demo" : "Preparation workspace"}
            </span>
            <span aria-hidden="true" className="hidden text-line sm:inline">
              /
            </span>
            <span className="truncate text-sm font-medium">{current}</span>
          </div>
          {onLeave && (
            <Button
              variant="ghost"
              disabled={busy}
              onClick={onLeave}
              className="shrink-0 px-2 text-xs"
            >
              <Icon name="exit" width={17} height={17} />
              {mode === "demo" ? "Exit and delete demo" : "Sign out"}
            </Button>
          )}
        </header>
        {mode === "demo" && (
          <aside
            aria-label="Demo disclosure"
            className="border-b border-[#ddd2b5] bg-[#f7f2e5] px-6 py-3 text-[#675020] sm:px-8 lg:px-10"
          >
            <p className="text-xs leading-6">
              <strong>Fictional demo data · simulated history.</strong> Aarav is
              a fictional candidate; no real platform usage or AI evaluation.
              You can upload your own resume in Resume. Your uploads and
              practice stay private to this browser session; access expires
              within 24 hours.
            </p>
          </aside>
        )}
        <main
          ref={main}
          id="main-content"
          tabIndex={-1}
          className="mx-auto max-w-6xl px-5 py-8 focus:outline-none sm:px-8 lg:px-10 lg:py-10"
        >
          {children}
        </main>
        <footer className="mx-5 mt-8 flex flex-wrap justify-between gap-3 border-t border-line py-5 text-xs leading-6 text-muted sm:mx-8 lg:mx-10">
          <span>
            Interview Prep ·{" "}
            {mode === "demo"
              ? "Temporary practice workspace"
              : "Private preparation workspace"}
          </span>
          <Link href="/privacy" className="underline underline-offset-4">
            Privacy & data
          </Link>
        </footer>
      </div>
      <Dialog
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        title="Navigation"
      >
        <div className="max-h-[75dvh] overflow-y-auto pt-4">
          <WorkspaceNav
            mode={mode}
            pathname={pathname}
            onNavigate={() => setMenuOpen(false)}
          />
        </div>
      </Dialog>
    </div>
  );
}
