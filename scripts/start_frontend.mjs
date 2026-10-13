import { cp } from "node:fs/promises";
import { existsSync } from "node:fs";

const frontend = new URL("../frontend/", import.meta.url);
const standalone = new URL(".next/standalone/frontend/", frontend);
const server = new URL("server.js", standalone);
if (!existsSync(server)) {
  throw new Error(
    "Production build is missing. Run pnpm build before pnpm start.",
  );
}

// Next.js standalone output needs static/public assets alongside its server.
await cp(
  new URL(".next/static/", frontend),
  new URL(".next/static/", standalone),
  {
    recursive: true,
  },
);
if (existsSync(new URL("public/", frontend))) {
  await cp(new URL("public/", frontend), new URL("public/", standalone), {
    recursive: true,
  });
}
process.env.HOSTNAME = process.env.FRONTEND_HOSTNAME ?? "127.0.0.1";
process.env.PORT ??= "3000";
await import(server.href);
