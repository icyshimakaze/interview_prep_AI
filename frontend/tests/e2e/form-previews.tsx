import { ProfileForm } from "@/components/workspace/profile-form";
import { TargetForm } from "@/components/workspace/target-form";
import { ResumeUpload } from "@/components/workspace/resume-upload";
import { ResumeEvidence } from "@/components/workspace/resume-evidence";
import { EvidenceForm } from "@/components/workspace/evidence-form";
import { SkillMatrixTable } from "@/components/workspace/skill-matrix";
import { resumeFixture } from "../resume-fixture";
import { matrix } from "../skill-fixture";
import { renderUiPreview } from "../ui-preview";

export function accountFormPreview(
  name: "profile" | "target" | "resume" | "skills",
): string {
  const form = {
    profile: <ProfileForm profile={null} onSave={async () => undefined} />,
    target: (
      <TargetForm
        target={null}
        onSave={async () => undefined}
        onCancel={() => undefined}
      />
    ),
    resume: (
      <>
        <ResumeUpload busy={false} onUpload={async () => undefined} />
        <section className="section-rule">
          <h2 className="section-title">Review your evidence</h2>
          <ResumeEvidence
            resume={resumeFixture}
            busy={false}
            onEdit={() => undefined}
            onDelete={() => undefined}
          />
          <EvidenceForm
            evidence={resumeFixture.evidence[0]}
            busy={false}
            onSave={async () => undefined}
            onReload={async () => undefined}
          />
        </section>
      </>
    ),
    skills: <SkillMatrixTable matrix={matrix} />,
  };
  return renderUiPreview(
    name,
    <>
      <h1 className="page-title mb-8">{name} form preview</h1>
      {form[name]}
    </>,
  );
}
