const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
    },
  );

  if (!response.ok) {
    const body = await response.text();

    throw new Error(
      body || `API request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

type ApiOptions = RequestInit & {
  accessToken?: string;
};

export async function api<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const {
    accessToken,
    headers,
    ...requestOptions
  } = options;

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...requestOptions,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken
          ? {
              Authorization: `Bearer ${accessToken}`,
            }
          : {}),
        ...headers,
      },
    },
  );

  if (response.status === 401 && accessToken) {
    window.sessionStorage.removeItem("access_token");

    throw new Error(
      "Your session has expired. Please login again.",
    );
  }

  if (!response.ok) {
    let message = "Something went wrong";

    try {
      const data = await response.json();

      if (typeof data.detail === "string") {
        message = data.detail;
      }
    } catch {
      // Ignore JSON parsing failures.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}
