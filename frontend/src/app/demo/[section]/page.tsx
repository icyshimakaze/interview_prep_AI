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
    title: `${workspaceSections.find((item) => item.slug === section)?.label ?? "Workspace"} demo`,
  };
}
export default async function DemoSectionPage({ params }: Props) {
  const { section } = await params;
  if (section === "dashboard") redirect("/demo");
  if (!isWorkspaceSection(section)) notFound();
  return <WorkspaceScreen section={section} />;
}
