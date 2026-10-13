import { ButtonLink } from "@/components/ui/button";
export default function NotFound() {
  return (
    <>
      <p className="eyebrow">Section not found</p>
      <h1 className="page-title">Let’s get back to your preparation.</h1>
      <p className="page-description">This workspace section doesn’t exist.</p>
      <ButtonLink href="/app/dashboard" className="mt-6">
        Back to dashboard
      </ButtonLink>
    </>
  );
}
