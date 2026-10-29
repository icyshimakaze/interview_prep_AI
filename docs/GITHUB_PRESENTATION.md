# Repository presentation and default-branch transition

Prepared 30 October 2026. These are reviewable recommendations; repository
settings, topics, social preview and default branch have not been changed. The
user has separately authorized publication of the documentation-only branch and
a reviewable PR. Production remains closed/demo; no merge or settings change is
authorized.

## Suggested About settings

**Description:** Interview preparation workspace with resume evidence, objective
assessments, mock interviews and Project Defense. Next.js, FastAPI and
PostgreSQL; includes an isolated demo with simulated feedback.

**Website:** <https://interviewprepai.webredirect.org>

**Topics:** `interview-preparation`, `technical-interviews`, `nextjs`, `react`,
`typescript`, `fastapi`, `python`, `postgresql`, `better-auth`, `full-stack`,
`learning-tools`, `portfolio-project`.

Use the repository's About editor to apply reviewed text and topics. Avoid AI
accuracy, hiring-success, traffic or coverage badges without traceable evidence.
The README's badges identify technologies and do not claim passing CI.
[GitHub topic guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).

## Social preview recommendation

Prepare a 1280 × 640 PNG under 1 MB with a solid light background, the project
name, a short description and a legible inset of an actual sanitized product
capture. The [desktop product capture](screenshots/preview-landing-desktop.png)
and its [provenance](screenshots/README.md) provide a source. Preserve the
visible simulation/preview meaning; include no provider screen, private record,
token, testimonial or fabricated result. Keep important content away from the
edges.

After review, upload the image through **Settings → Social preview**. A cropped
product image should still be described as a product view, not as evidence of
real AI evaluation or public account availability.
[GitHub social-preview requirements](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).

## Make the modern application the repository homepage

GitHub metadata confirms that the default branch is currently `main`, which
contains the retired Python prototype. The modern source is published on
`release/github-only-public-2026-10-30-37bbc9a5`; this portfolio branch is based
on its exact `dbbe982186373ccaea1c7a34bd60a3d9f0f5d3a3` commit.

Changing a README on another branch does not change the default repository view.
After a successful authorized release and documentation review:

1. Select a durable modern branch and review its source, migrations, CI and
   documentation. Publish the documentation branch and open a PR **against the
   modern branch**, keeping the diff limited to documentation and screenshots.
   Do not target the retired `main` with a misleading documentation-only PR.
2. Check Vercel's production Git binding, Render's manual-deploy configuration,
   branch protections and CI rules before changing any branch setting. The old
   production branch must not be rebuilt blindly against the 0013 database.
3. With separate maintainer authorization, merge the reviewed documentation and
   set the durable modern branch in **Settings → Default branch**. GitHub
   requires repository admin access. Update clone instructions only after
   verifying the actual transition.
4. Keep the legacy prototype and its history available. If retaining `main` as
   the default is preferred, prepare a separately reviewed application migration
   PR into it instead; that is a larger source/history decision.

No merge, force-push, default-branch change, automatic release or deletion is
part of this documentation preparation.
[GitHub default-branch instructions](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/changing-the-default-branch).

## Published PR

[Review documentation PR #1](https://github.com/icyshimakaze/interview_prep_AI/pull/1).
It is open and unmerged; the default branch remains `main`.

**Title:** Document the modern application and recruiter walkthrough

**Base:** `release/github-only-public-2026-10-30-37bbc9a5`

**Head:** `docs/portfolio-homepage-2026-10-30` (documentation-only publication)

The PR description and validation record accompany the documentation
publication. The earlier publication hold was superseded by the user's explicit
approval on 30 October 2026. Public account registration remains unlaunched. A
temporary release branch need not become the permanent default; the maintainer
should explicitly choose the durable branch.
