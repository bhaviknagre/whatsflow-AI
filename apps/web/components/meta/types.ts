export {};

declare global {
  interface Window {
    FB?: {
      init: (options: {
        appId: string;
        cookie: boolean;
        xfbml: boolean;
        version: string;
      }) => void;

      login: (
        callback: (response: {
          authResponse?: {
            code?: string;
            accessToken?: string;
          };
          status?: string;
        }) => void,
        options?: Record<string, unknown>,
      ) => void;
    };

    fbAsyncInit?: () => void;
  }
}
