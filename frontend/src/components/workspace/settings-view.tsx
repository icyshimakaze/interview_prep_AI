import Link from "next/link";
import type { WorkspaceContextValue } from "./workspace-context";
import { ProfileForm } from "./profile-form";
import { SectionHeader } from "./section-header";
import { Badge } from "@/components/ui/table";
import { ProfileDeletion } from "./profile-deletion";

export function SettingsView({
  data,
  onSaveProfile,
  onReload,
  onDeleteProfile,
  busy,
}: WorkspaceContextValue) {
  const profile = data.profile;
  return (
    <>
      <SectionHeader
        title="Settings / Profile"
        eyebrow="Make it your own"
        description="Your preparation direction, study preferences, and account information."
      />
      {data.mode === "account" && onSaveProfile ? (
        <ProfileForm
          key={profile?.id ?? "new-profile"}
          profile={profile}
          onSave={onSaveProfile}
          onReload={onReload}
        />
      ) : (
        <section className="border-y border-line bg-surface p-6 sm:p-8">
          <div className="flex flex-wrap justify-between gap-4">
            <h2 className="section-title">Sample preparation profile</h2>
            <Badge tone="amber">Fictional · Read only</Badge>
          </div>
          <p className="mt-3 text-sm leading-7 text-muted">
            This profile belongs to the fictional demo candidate. Create an
            account when sign-up is available to save your own preparation
            preferences.
          </p>
          <dl className="mt-6 grid gap-6 sm:grid-cols-2">
            {[
              ["Display name", profile?.display_name ?? "Not provided"],
              ["Target role", profile?.target_role ?? "Not provided"],
              ["Experience level", profile?.experience_band ?? "Not provided"],
              ["Timezone", profile?.timezone ?? "Not provided"],
              [
                "Weekly study budget",
                profile ? `${profile.weekly_minutes} minutes` : "Not set",
              ],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs text-muted">{label}</dt>
                <dd className="mt-2 text-sm font-medium">{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}
      {data.mode === "account" && profile && onDeleteProfile && (
        <ProfileDeletion
          onDelete={onDeleteProfile}
          onReload={onReload}
          disabled={busy}
        />
      )}
      <section className="form-section">
        <div>
          <h2 className="section-title">Privacy & account</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Understand what is saved and which controls are available.
          </p>
        </div>
        <div className="sm:col-span-1">
          <div className="sm:col-span-2">
            <h3 className="text-sm font-semibold">
              {data.mode === "demo"
                ? "A temporary workspace"
                : "Account access"}
            </h3>
            <p className="mt-2 text-sm leading-7 text-muted">
              {data.mode === "demo"
                ? "Use “Exit and delete demo” above to erase this workspace. Otherwise it expires within 24 hours and is removed by hourly cleanup."
                : "Sign-in is managed by Clerk. Use Sign out above to leave your account. Your saved preparation profile remains in the application database."}
            </p>
            <h3 className="mt-6 text-sm font-semibold">Data controls</h3>
            <p className="mt-2 text-sm leading-7 text-muted">
              Self-service account export and deletion are not yet available in
              this preview. Real files and AI processing are not enabled.
            </p>
            <Link href="/privacy" className="text-link mt-3">
              Read privacy & data details
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
