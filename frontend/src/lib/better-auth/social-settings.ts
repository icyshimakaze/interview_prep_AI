export type SocialProviderName = "google" | "github";

export interface SocialEnvironment {
  SOCIAL_REGISTRATION_MODE?: string;
  GOOGLE_AUTH_ENABLED?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  GOOGLE_ALLOWED_SUBJECTS?: string;
  GITHUB_AUTH_ENABLED?: string;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
  GITHUB_ALLOWED_SUBJECTS?: string;
}

interface ProviderSettings {
  clientId: string;
  clientSecret: string;
  allowedSubjects: readonly string[];
  publicRegistration?: boolean;
}
export interface SocialSettings {
  google?: ProviderSettings;
  github?: ProviderSettings;
}

function enabled(value: string | undefined): boolean {
  if (value && value !== "false" && value !== "true")
    throw new Error("Social authentication flags must be true or false.");
  return value === "true";
}

function providerSettings(
  clientId: string | undefined,
  clientSecret: string | undefined,
  subjects: string | undefined,
  github: boolean,
  publicRegistration: boolean,
): ProviderSettings {
  if (
    !clientId?.trim() ||
    !clientSecret?.trim() ||
    clientId.length > 512 ||
    clientSecret.length > 2048 ||
    !(github
      ? /^[A-Za-z0-9_.-]{16,512}$/.test(clientId)
      : /^[A-Za-z0-9_-]+\.apps\.googleusercontent\.com$/.test(clientId)) ||
    !/^[A-Za-z0-9_.-]{16,2048}$/.test(clientSecret) ||
    /\s/.test(clientId + clientSecret) ||
    /REPLACE_WITH|YOUR_/.test(clientId + clientSecret)
  )
    throw new Error(
      "Enabled social providers require complete server credentials.",
    );
  let input: unknown;
  try {
    if ((!subjects && !publicRegistration) || (subjects?.length ?? 0) > 16384)
      throw new Error();
    input = JSON.parse(subjects || "[]");
  } catch {
    throw new Error(
      "Enabled social providers require a bounded stable-identity allowlist.",
    );
  }
  if (
    !Array.isArray(input) ||
    (publicRegistration ? input.length !== 0 : input.length < 1) ||
    input.length > 32 ||
    !input.every(
      (item: unknown): item is string =>
        typeof item === "string" &&
        (github
          ? /^[1-9][0-9]{0,19}$/.test(item)
          : /^[A-Za-z0-9_-]{1,255}$/.test(item)),
    ) ||
    new Set(input).size !== input.length
  )
    throw new Error(
      "Social admission requires distinct provider subjects, never email addresses.",
    );
  return { clientId, clientSecret, allowedSubjects: input, publicRegistration };
}

export function socialAuthSettings(env: SocialEnvironment): SocialSettings {
  const mode = env.SOCIAL_REGISTRATION_MODE ?? "invited";
  if (mode !== "invited" && mode !== "public")
    throw new Error("Social registration mode must be invited or public.");
  const result: SocialSettings = {};
  if (enabled(env.GOOGLE_AUTH_ENABLED))
    result.google = providerSettings(
      env.GOOGLE_CLIENT_ID,
      env.GOOGLE_CLIENT_SECRET,
      env.GOOGLE_ALLOWED_SUBJECTS,
      false,
      mode === "public",
    );
  if (enabled(env.GITHUB_AUTH_ENABLED))
    result.github = providerSettings(
      env.GITHUB_CLIENT_ID,
      env.GITHUB_CLIENT_SECRET,
      env.GITHUB_ALLOWED_SUBJECTS,
      true,
      mode === "public",
    );
  return result;
}

export function socialProviderNames(
  settings: SocialSettings = {},
): SocialProviderName[] {
  return (["google", "github"] as const).filter((name) =>
    Boolean(settings[name]),
  );
}

export function admittedSocialIdentity(
  settings: SocialSettings,
  provider: string,
  profile: Record<string, unknown> | undefined,
): boolean {
  if (provider === "google") {
    const subject = profile?.sub;
    return (
      typeof subject === "string" &&
      /^[A-Za-z0-9_-]{1,255}$/.test(subject) &&
      Boolean(
        settings.google &&
        (settings.google.publicRegistration === true ||
          settings.google.allowedSubjects.includes(subject)),
      )
    );
  }
  if (provider === "github") {
    const subject = githubSubject(profile?.id);
    return (
      subject !== undefined &&
      Boolean(
        settings.github &&
        (settings.github.publicRegistration === true ||
          settings.github.allowedSubjects.includes(subject)),
      )
    );
  }
  return false;
}

// GitHub returns an integer ID in JSON. Never use mutable login/email as a key.
export function githubSubject(value: unknown): string | undefined {
  if (typeof value === "number")
    return Number.isSafeInteger(value) && value > 0 ? String(value) : undefined;
  return typeof value === "string" && /^[1-9][0-9]{0,19}$/.test(value)
    ? value
    : undefined;
}

export const SOCIAL_SUCCESS_PATH = "/app/dashboard";
export const SOCIAL_LINK_PATH = "/app/account-access";
export const SOCIAL_ERROR_PATH = "/sign-in?social_error=1";
export const SOCIAL_FRESH_SECONDS = 300;
