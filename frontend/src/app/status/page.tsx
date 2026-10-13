import type { Metadata } from "next";
import { PublicShell } from "@/components/public/public-shell";
import { ServiceStatus } from "@/components/service-status";

export const metadata: Metadata = { title: "Service status" };
export default function StatusPage() {
  return (
    <PublicShell>
      <div className="public-width py-16">
        <div className="max-w-2xl">
          <p className="eyebrow">System information</p>
          <h1 className="page-title">Service status</h1>
          <p className="page-description">
            Run a live check of the application and its database. This reports
            the current connection, not historical uptime.
          </p>
          <section className="section-rule">
            <h2 className="section-title mb-5">Service connectivity</h2>
            <ServiceStatus />
          </section>
        </div>
      </div>
    </PublicShell>
  );
}
