import { notFound, redirect } from "next/navigation";
import {
  isWorkspaceSection,
  workspaceSections,
} from "@/components/workspace/navigation";
import { WorkspaceScreen } from "@/components/workspace/workspace-context";

type Props = { params: Promise<{ section: string }> };
export async function generateMetadata({ params }: Props) {
  const { section } = await params;
  return {
    title:
      workspaceSections.find((item) => item.slug === section)?.label ??
      "Workspace",
  };
}
export default async function WorkspacePage({ params }: Props) {
  const { section } = await params;
  if (section === "profile") redirect("/app/settings");
  if (section === "practice") redirect("/app/questions");
  if (!isWorkspaceSection(section)) notFound();
  return <WorkspaceScreen section={section} />;
}
