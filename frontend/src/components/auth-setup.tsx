import { PublicShell } from "@/components/public/public-shell";
import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";

export function AuthSetup() {
  return (
    <PublicShell>
      <div className="public-width grid gap-10 py-16 sm:py-24 md:grid-cols-[1fr_1.2fr]">
        <div>
          <p className="eyebrow">Your preparation workspace</p>
          <h1 className="editorial-title mt-5">
            Account sign-in is unavailable
          </h1>
        </div>
        <div className="border-l-2 border-line pl-6 sm:pl-9">
          <Icon name="lock" width={28} height={28} className="text-accent" />
          <p className="mt-6 text-base leading-8 text-muted">
            Account access isn’t configured for this preview. Explore the
            interactive demo with a fictional candidate; no sign-up or AI key is
            needed.
          </p>
          <p className="mt-4 text-sm leading-7 text-muted">
            The demo includes labeled sample history, resume evidence, and a
            roadmap you can try. Your demo workspace stays separate from real
            accounts.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <ButtonLink href="/demo">Try Interactive Demo</ButtonLink>
            <ButtonLink href="/" variant="outline">
              Back home
            </ButtonLink>
          </div>
        </div>
      </div>
    </PublicShell>
  );
}
