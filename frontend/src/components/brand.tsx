import Link from "next/link";

export function Brand() {
  return (
    <Link
      href="/"
      aria-label="Interview Prep home"
      className="inline-flex min-h-11 shrink-0 items-center gap-2.5 text-base font-semibold tracking-tight"
    >
      <span
        aria-hidden="true"
        className="flex h-8 w-8 items-center justify-center rounded-sm bg-accent font-serif text-lg text-white"
      >
        ip<span className="text-[#cfddbd]">.</span>
      </span>
      Interview Prep
    </Link>
  );
}
