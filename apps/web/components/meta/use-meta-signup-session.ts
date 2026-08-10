"use client";

import { useEffect, useState } from "react";

interface SignupSession {
  wabaId: string | null;
  phoneNumberId: string | null;
}

interface MetaSignupMessage {
  type?: string;
  event?: string;
  data?: {
    waba_id?: string;
    phone_number_id?: string;
  };
}

export function useMetaSignupSession() {
  const [
    session,
    setSession,
  ] = useState<SignupSession>({
    wabaId: null,
    phoneNumberId: null,
  });

  useEffect(() => {
    function handleMessage(
      event: MessageEvent,
    ) {
      /*
       * Only accept messages from Meta.
       */
      if (
        event.origin !==
        "https://www.facebook.com"
      ) {
        return;
      }

      if (
        typeof event.data !==
        "string"
      ) {
        return;
      }

      let message:
        | MetaSignupMessage
        | null = null;

      try {
        message =
          JSON.parse(event.data);
      } catch {
        return;
      }

      if (!message) {
        return;
      }

      const data =
        message.data;

      if (!data) {
        return;
      }

      if (
        data.waba_id &&
        data.phone_number_id
      ) {
        setSession({
          wabaId:
            data.waba_id,
          phoneNumberId:
            data.phone_number_id,
        });
      }
    }

    window.addEventListener(
      "message",
      handleMessage,
    );

    return () => {
      window.removeEventListener(
        "message",
        handleMessage,
      );
    };
  }, []);

  return session;
}