import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdom lacks native dialog lifecycle methods. Browser tests exercise actual
// modal focus, Escape, overflow and focus restoration in Chrome.
HTMLDialogElement.prototype.showModal = function () {
  this.setAttribute("open", "");
};
HTMLDialogElement.prototype.close = function () {
  this.removeAttribute("open");
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
