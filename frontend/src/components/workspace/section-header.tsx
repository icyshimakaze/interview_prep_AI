import type { ReactNode } from "react";
import { Badge } from "@/components/ui/table";

export function SectionHeader({
  title,
  description,
  eyebrow = "Preparation workspace",
  unavailable = false,
  action,
}: {
  title: string;
  description: string;
  eyebrow?: string;
  unavailable?: boolean;
  action?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="page-title">{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action ?? (unavailable && <Badge>In development</Badge>)}
    </header>
  );
}
