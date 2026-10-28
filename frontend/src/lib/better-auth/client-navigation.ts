"use client";

// Identity changes must discard the previous account's Router Cache and UI.
export function navigateAfterAuthentication(
  path: "/" | "/app/dashboard",
): void {
  window.location.replace(path);
}
