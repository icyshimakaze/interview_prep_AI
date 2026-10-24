import { cp } from "node:fs/promises";
import { existsSync } from "node:fs";
import { loadEnvFile } from "node:process";

const frontend = new URL("../frontend/", import.meta.url);
const localEnvironment = new URL(".env.local", frontend);
if (existsSync(localEnvironment)) loadEnvFile(localEnvironment);
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
// Match NextURL's loopback normalization so Clerk's internal rewrites stay local.
process.env.HOSTNAME = process.env.FRONTEND_HOSTNAME ?? "localhost";
process.env.PORT ??= "3000";
await import(server.href);
