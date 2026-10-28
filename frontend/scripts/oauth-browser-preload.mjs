// Only an explicitly invoked, owned local test server may install this transport.
import { installSyntheticOAuth } from "./oauth-test-transport.mjs";
const origin = new URL(process.env.BETTER_AUTH_URL ?? "http://invalid");
const database = new URL(process.env.AUTH_DATABASE_URL ?? "http://invalid");
if (
  process.env.APP_ENV !== "test" ||
  process.env.AUTH_PROVIDER !== "better_auth" ||
  origin.protocol !== "http:" ||
  origin.hostname !== "localhost" ||
  !["localhost", "127.0.0.1"].includes(database.hostname) ||
  !database.pathname.endsWith("_test")
)
  throw new Error("Synthetic OAuth preload refuses non-owned targets");
installSyntheticOAuth({ browser: true });
