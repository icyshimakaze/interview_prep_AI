import type { ComponentProps } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import Link from "next/link.js";

const buttonVariants = cva(
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60",
  {
    variants: {
      variant: {
        default: "bg-accent text-white hover:bg-accent-hover",
        outline: "border border-line bg-surface text-ink hover:bg-paper",
        ghost: "text-ink hover:bg-paper",
        danger: "bg-danger text-white hover:bg-red-900",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

type ButtonProps = ComponentProps<"button"> &
  VariantProps<typeof buttonVariants>;

export function Button({
  className,
  variant,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(buttonVariants({ variant }), className)}
      {...props}
    />
  );
}

export function ButtonLink({
  className,
  variant,
  ...props
}: ComponentProps<typeof Link> & VariantProps<typeof buttonVariants>) {
  return (
    <Link className={cn(buttonVariants({ variant }), className)} {...props} />
  );
}
