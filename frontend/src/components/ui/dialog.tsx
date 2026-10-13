"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { Button } from "./button";
import { Icon } from "./icon";

export function Dialog({
  open,
  onClose,
  title,
  children,
  busy = false,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!open || !dialog) return;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.showModal();
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
      if (previousFocus instanceof HTMLElement) previousFocus.focus();
    };
  }, [open]);
  return (
    <dialog
      ref={ref}
      className="dialog max-h-[90dvh] overflow-y-auto"
      aria-labelledby={titleId}
      onKeyDown={(event) => {
        if (event.key !== "Tab") return;
        const focusable = Array.from(
          event.currentTarget.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
          ),
        ).filter((element) => element.getClientRects().length > 0);
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (!first || !last) {
          event.preventDefault();
          return;
        }
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        }
        if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <h2 id={titleId} className="section-title">
          {title}
        </h2>
        <Button
          variant="ghost"
          aria-label="Close dialog"
          disabled={busy}
          onClick={onClose}
          className="-mt-2 -mr-2 px-3"
        >
          <Icon name="close" />
        </Button>
      </div>
      {children}
    </dialog>
  );
}
