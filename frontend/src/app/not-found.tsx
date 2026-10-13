import { PublicShell } from "@/components/public/public-shell";
import { ButtonLink } from "@/components/ui/button";
export default function NotFound() {
  return (
    <PublicShell>
      <div className="public-width py-24">
        <p className="eyebrow">Page not found</p>
        <h1 className="editorial-title mt-5">Let’s find your way back.</h1>
        <p className="mt-5 text-muted">
          This page doesn’t exist or may have moved.
        </p>
        <ButtonLink href="/" className="mt-8">
          Back to Interview Prep
        </ButtonLink>
      </div>
    </PublicShell>
  );
}
