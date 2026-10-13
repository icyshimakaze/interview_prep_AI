import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ServiceStatus } from "@/components/service-status";

describe("service connectivity", () => {
  it("verifies live API/database readiness with an accessible control", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      Response.json({
        status: "ok",
        service: "interview-prep-api",
        database: "connected",
        schema_revision: "0002_relational_model",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<ServiceStatus />);
    const user = userEvent.setup();
    await user.tab();
    expect(
      screen.getByRole("button", { name: "Verify connection" }),
    ).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(
      await screen.findByText("API connected · PostgreSQL connected"),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/health/ready",
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("shows failure and supports retry without claiming a connection", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response("", { status: 503 })),
    );
    render(<ServiceStatus />);
    await userEvent.click(
      screen.getByRole("button", { name: "Verify connection" }),
    );
    expect(
      await screen.findByText(/API or database is not ready/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
    expect(
      screen.queryByText("API connected · PostgreSQL connected"),
    ).not.toBeInTheDocument();
  });

  it("rejects malformed success responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(Response.json({ status: "ok" })),
    );
    render(<ServiceStatus />);
    await userEvent.click(
      screen.getByRole("button", { name: "Verify connection" }),
    );
    expect(
      await screen.findByText(/unexpected health response/),
    ).toBeInTheDocument();
  });

  it("handles network failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn<typeof fetch>()
        .mockRejectedValue(new TypeError("Network unavailable")),
    );
    render(<ServiceStatus />);
    await userEvent.click(
      screen.getByRole("button", { name: "Verify connection" }),
    );
    expect(await screen.findByText("Network unavailable")).toBeInTheDocument();
  });
});
