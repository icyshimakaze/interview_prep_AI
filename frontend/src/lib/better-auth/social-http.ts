import {
  SOCIAL_ERROR_PATH,
  SOCIAL_LINK_PATH,
  SOCIAL_SUCCESS_PATH,
  type SocialProviderName,
  type SocialSettings,
} from "./social-settings";

export function socialProviderEnabled(
  settings: SocialSettings | undefined,
  value: unknown,
): value is SocialProviderName {
  return (
    (value === "google" || value === "github") && Boolean(settings?.[value])
  );
}

export function socialRequestBody(
  values: Record<string, unknown>,
  origin: string,
  link: boolean,
  settings: SocialSettings | undefined,
): Record<string, unknown> | undefined {
  const success = link ? SOCIAL_LINK_PATH : SOCIAL_SUCCESS_PATH;
  const allowed = new Set([
    "provider",
    "callbackURL",
    "newUserCallbackURL",
    "errorCallbackURL",
    "disableRedirect",
  ]);
  if (
    !socialProviderEnabled(settings, values.provider) ||
    Object.keys(values).some((key) => !allowed.has(key))
  )
    return undefined;
  for (const [key, path] of [
    ["callbackURL", success],
    ["newUserCallbackURL", success],
    ["errorCallbackURL", SOCIAL_ERROR_PATH],
  ] as const) {
    if (
      values[key] !== undefined &&
      values[key] !== path &&
      values[key] !== origin + path
    )
      return undefined;
  }
  if (
    values.disableRedirect !== undefined &&
    typeof values.disableRedirect !== "boolean"
  )
    return undefined;
  return {
    provider: values.provider,
    callbackURL: origin + success,
    newUserCallbackURL: origin + success,
    errorCallbackURL: origin + SOCIAL_ERROR_PATH,
    ...(values.disableRedirect === undefined
      ? {}
      : { disableRedirect: values.disableRedirect }),
  };
}

export function validSocialCallback(url: URL): boolean {
  // Response metadata is bounded but never used as identity or scope evidence.
  const allowed = new Set([
    "code",
    "state",
    "error",
    "error_description",
    "error_uri",
    "iss",
    "scope",
    "authuser",
    "prompt",
    "hd",
  ]);
  return (
    url.search.length <= 8192 &&
    [...url.searchParams.keys()].every((key) => allowed.has(key)) &&
    new Set(url.searchParams.keys()).size === url.searchParams.size
  );
}

export function safeSocialLocation(
  location: string | null,
  origin: string,
): string {
  if (
    location === origin + SOCIAL_SUCCESS_PATH ||
    location === origin + SOCIAL_LINK_PATH
  )
    return location;
  return origin + SOCIAL_ERROR_PATH;
}
