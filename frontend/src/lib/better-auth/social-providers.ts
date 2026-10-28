import { google, github } from "better-auth/social-providers";
import { verifyProviderIdToken } from "better-auth/oauth2";
import { githubSubject, type SocialSettings } from "./social-settings";

// Google claims require the pinned provider's supported cryptographic verifier.
// GitHub identity is retrieved through its authenticated HTTPS APIs instead.
export function configuredSocialProviders(settings: SocialSettings = {}) {
  const googleOptions = settings.google && {
    clientId: settings.google.clientId,
    clientSecret: settings.google.clientSecret,
    disableDefaultScope: true,
    scope: ["openid", "profile", "email"],
    prompt: "select_account" as const,
    accessType: "online" as const,
    includeGrantedScopes: false,
  };
  const githubOptions = settings.github && {
    clientId: settings.github.clientId,
    clientSecret: settings.github.clientSecret,
    disableDefaultScope: true,
    scope: ["user:email"],
    prompt: "select_account" as const,
  };
  const googleProvider = googleOptions && google(googleOptions);
  const githubProvider = githubOptions && github(githubOptions);
  return {
    ...(googleOptions && googleProvider
      ? {
          google: {
            ...googleOptions,
            getUserInfo: async (
              token: Parameters<typeof googleProvider.getUserInfo>[0],
            ) => {
              if (
                !token.idToken ||
                !(await verifyProviderIdToken(googleProvider, token.idToken))
              )
                return null;
              const result = await googleProvider.getUserInfo(token);
              if (
                !result ||
                (settings.google?.publicRegistration === true &&
                  (!result.user.email ||
                    result.user.email.length > 254 ||
                    result.user.emailVerified !== true))
              )
                return null;
              return {
                user: {
                  name: result.user.name || "Candidate",
                  email: result.user.email,
                  emailVerified: result.user.emailVerified === true,
                  image: undefined,
                },
                data: result.data,
              };
            },
          },
        }
      : {}),
    ...(githubOptions && githubProvider
      ? {
          github: {
            ...githubOptions,
            getUserInfo: async (
              token: Parameters<typeof githubProvider.getUserInfo>[0],
            ) => {
              // GitHub uses authenticated HTTPS user/email APIs, not OIDC ID tokens.
              // The built-in provider retrieves private email via /user/emails.
              if (!token.accessToken) return null;
              const result = await githubProvider.getUserInfo(token);
              if (
                !result ||
                !githubSubject(result.data.id) ||
                !result.user.email ||
                result.user.email.length > 254 ||
                (settings.github?.publicRegistration === true &&
                  result.user.emailVerified !== true)
              )
                return null;
              return {
                user: {
                  name: result.user.name || "Candidate",
                  email: result.user.email,
                  emailVerified: result.user.emailVerified === true,
                  image: undefined,
                },
                data: result.data,
              };
            },
          },
        }
      : {}),
  };
}
