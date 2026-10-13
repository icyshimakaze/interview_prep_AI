import { ButtonLink } from "@/components/ui/button";
export default function NotFound() {
  return (
    <>
      <p className="eyebrow">Section not found</p>
      <h1 className="page-title">Let’s get back to the demo.</h1>
      <p className="page-description">This demo section doesn’t exist.</p>
      <ButtonLink href="/demo" className="mt-6">
        Back to demo
      </ButtonLink>
    </>
  );
}
