import type { ReactNode } from "react";
import { DemoWorkspace } from "@/components/demo-workspace";
export default function DemoLayout({ children }: { children: ReactNode }) {
  return <DemoWorkspace>{children}</DemoWorkspace>;
}
