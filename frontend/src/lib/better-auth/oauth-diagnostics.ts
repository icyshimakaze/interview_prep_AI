import { randomUUID } from "node:crypto";
import type { SocialProviderName } from "./social-settings";
import { SOCIAL_LINK_PATH, SOCIAL_SUCCESS_PATH } from "./social-settings";

// Only fixed protocol/library codes may reach logs. Never forward a provider's
// description, request URL, state, code, profile, email, cookie or exception.
const failureCodes = new Set([
  "access_denied",
  "account_not_linked",
  "account_already_linked_to_different_user",
  "account_hook_binding_conflict",
  "email_not_found",
  "email_not_verified",
  "invalid_callback_request",
  "invalid_code",
  "issuer_missing",
  "issuer_mismatch",
  "no_code",
  "nonce_binding_missing",
  "oauth_provider_not_found",
  "signup_disabled",
  "social_admission_closed",
  "social_provider_state_mismatch",
  "social_link_requires_recent_session",
  "state_invalid",
  "state_mismatch",
  "state_not_found",
  "unable_to_create_user",
  "unable_to_get_user_info",
  "unable_to_link_account",
  "unable_to_update_account",
  "unable_to_create_session",
]);

export function oauthCallbackReason(
  status: number,
  location: string | null,
  origin: string,
): string {
  if (status >= 500) return "auth_unavailable";
  if (status < 300 || status >= 400) return "callback_request_rejected";
  if (
    location === origin + SOCIAL_SUCCESS_PATH ||
    location === origin + SOCIAL_LINK_PATH
  )
    return "completed";
  try {
    const url = new URL(location ?? "");
    if (
      url.origin !== origin ||
      url.pathname !== "/sign-in" ||
      url.searchParams.get("social_error") !== "1" ||
      url.searchParams.getAll("error").length !== 1
    )
      return "unclassified_callback_failure";
    const reason = url.searchParams.get("error") ?? "";
    return failureCodes.has(reason) ? reason : "unclassified_callback_failure";
  } catch {
    return "unclassified_callback_failure";
  }
}

export function recordOAuthCallback(
  provider: SocialProviderName,
  publicRegistration: boolean,
  status: number,
  location: string | null,
  origin: string,
): string {
  const requestId = randomUUID();
  const reason = oauthCallbackReason(status, location, origin);
  // One bounded record per callback, including successes for comparison. The
  // identifier is generated here; an untrusted caller cannot inject log fields.
  try {
    console.info(
      JSON.stringify({
        event: "oauth_callback_result",
        requestId,
        provider,
        admission: publicRegistration ? "public" : "invited",
        status,
        reason,
      }),
    );
  } catch {
    // An unavailable log sink must not change an authentication decision.
  }
  return requestId;
}
