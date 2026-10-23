import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdom lacks native dialog lifecycle methods. Browser tests exercise actual
// modal focus, Escape, overflow and focus restoration in Chrome.
if (typeof HTMLDialogElement !== "undefined") {
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute("open");
  };
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn<typeof fetch>()
      .mockRejectedValue(
        new Error(
          "Live fetch is forbidden in component tests; provide an explicit mock.",
        ),
      ),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
