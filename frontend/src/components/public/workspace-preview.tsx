import { Icon } from "@/components/ui/icon";

export function WorkspacePreview() {
  return (
    <figure className="border border-line bg-surface">
      <figcaption className="flex items-center justify-between gap-3 border-b border-line px-5 py-3 text-xs text-muted">
        <span>YOUR PREPARATION WORKSPACE</span>
        <span>Interface preview</span>
      </figcaption>
      <div className="p-6 sm:p-8">
        <div className="mb-6 flex items-center gap-2 text-xs text-muted">
          <Icon name="dashboard" width={16} height={16} /> Dashboard
        </div>
        <p className="font-serif text-2xl">Start with a direction.</p>
        <p className="mt-2 text-sm leading-6 text-muted">
          Your preparation begins with the role you want.
        </p>
        <div className="mt-7 border-l-2 border-accent bg-tint p-5">
          <div className="flex items-center gap-3 text-sm font-semibold">
            <span className="text-accent">01</span> Set up your profile
          </div>
          <p className="mt-2 pl-7 text-xs leading-6 text-muted">
            Your target role, experience, and study time.
          </p>
          <span className="mt-4 inline-flex items-center gap-2 pl-7 text-xs font-semibold text-accent">
            Your first step <Icon name="arrow" width={16} height={16} />
          </span>
        </div>
        <div className="mt-5 space-y-0">
          {["Bring your experience into focus", "Make space for practice"].map(
            (item, index) => (
              <div
                key={item}
                className="flex items-center gap-3 border-b border-line py-4 text-sm text-muted"
              >
                <span className="font-mono text-xs">0{index + 2}</span>
                {item}
              </div>
            ),
          )}
        </div>
        <p className="mt-6 text-xs leading-6 text-muted">
          No scores before you start. No progress without practice.
        </p>
      </div>
    </figure>
  );
}
