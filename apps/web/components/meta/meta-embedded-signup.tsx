"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function MetaEmbeddedSignup() {
  const router = useRouter();

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  async function connect() {
    setLoading(true);
    setError(null);

    try {
      const token =
        window.localStorage.getItem(
          "access_token",
        );

      if (!token) {
        throw new Error(
          "Please login before connecting WhatsApp.",
        );
      }

      /*
       * Step 1:
       * Ask our backend for a one-time OAuth state.
       */
      const stateResponse =
        await fetch(
          "/api/v1/whatsapp/connect",
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          },
        );

      if (!stateResponse.ok) {
        const body =
          await stateResponse.json();

        throw new Error(
          body.detail ??
            "Unable to initialize WhatsApp signup.",
        );
      }

      const {
        state,
      } = await stateResponse.json();

      /*
       * Step 2:
       * Make sure the Meta SDK is available.
       */
      if (!window.FB) {
        throw new Error(
          "Meta SDK is not ready. Please refresh the page and try again.",
        );
      }

      /*
       * Step 3:
       * Launch Meta Embedded Signup.
       */
      window.FB.login(
        async (result) => {
          try {
            if (
              !result.authResponse?.code
            ) {
              throw new Error(
                "Meta did not return an authorization code.",
              );
            }

            /*
             * The authorization code is exchanged
             * server-side.
             *
             * We intentionally do NOT send:
             *
             * - META_APP_SECRET
             * - access tokens
             *
             * to the browser.
             */
            const signupResponse =
              await fetch(
                "/api/v1/whatsapp/signup",
                {
                  method: "POST",
                  headers: {
                    "Content-Type":
                      "application/json",
                    Authorization:
                      `Bearer ${token}`,
                  },
                  body:
                    JSON.stringify({
                      code:
                        result.authResponse
                          .code,
                      state,

                      /*
                       * These are temporarily supplied
                       * by the Embedded Signup callback.
                       *
                       * We'll replace this with the
                       * official session-info extraction
                       * in the next step.
                       */
                      waba_id:
                        "",
                      phone_number_id:
                        "",
                    }),
                },
              );

            if (!signupResponse.ok) {
              const body =
                await signupResponse.json();

              throw new Error(
                body.detail ??
                  "Unable to complete WhatsApp signup.",
              );
            }

            setLoading(false);

            router.push(
              "/inbox?whatsapp=connected",
            );
          } catch (err) {
            setLoading(false);

            setError(
              err instanceof Error
                ? err.message
                : "WhatsApp signup failed.",
            );
          }
        },
        {
          config_id:
            process.env
              .NEXT_PUBLIC_META_EMBEDDED_SIGNUP_CONFIG_ID,

          response_type: "code",

          override_default_response_type:
            true,

          extras: {
            setup: {},

            featureType:
              "whatsapp_business_app_onboarding",

            sessionInfoVersion: "3",
          },
        },
      );
    } catch (err) {
      setLoading(false);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to start WhatsApp signup.",
      );
    }
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={connect}
        disabled={loading}
        className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {loading
          ? "Connecting..."
          : "Connect WhatsApp Business"}
      </button>

      {error && (
        <p className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}