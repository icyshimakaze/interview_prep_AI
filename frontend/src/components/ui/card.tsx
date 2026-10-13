import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: ComponentProps<"section">) {
  return (
    <section
      className={cn(
        "rounded-md border border-line bg-surface p-6 sm:p-8",
        className,
      )}
      {...props}
    />
  );
}
