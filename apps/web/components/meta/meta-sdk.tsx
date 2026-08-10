"use client";

import { useEffect } from "react";

export function MetaSDK() {
  useEffect(() => {
    if (window.FB) {
      return;
    }

    window.fbAsyncInit = () => {
      window.FB?.init({
        appId:
          process.env.NEXT_PUBLIC_META_APP_ID ?? "",
        cookie: true,
        xfbml: true,
        version: "v23.0",
      });
    };

    const existingScript =
      document.getElementById(
        "facebook-jssdk",
      );

    if (existingScript) {
      return;
    }

    const script =
      document.createElement("script");

    script.id = "facebook-jssdk";
    script.src =
      "https://connect.facebook.net/en_US/sdk.js";
    script.async = true;
    script.defer = true;

    document.body.appendChild(script);

    return () => {
      window.fbAsyncInit = undefined;
    };
  }, []);

  return null;
}