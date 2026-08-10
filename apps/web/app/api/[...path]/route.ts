import { NextRequest } from "next/server";

const API_URL =
  process.env.BACKEND_API_URL ?? "http://localhost:8000";

async function proxy(
  request: NextRequest,
  context: {
    params: Promise<{ path: string[] }>;
  },
) {
  const { path } = await context.params;

  const targetUrl = new URL(
    `/api/${path.join("/")}`,
    API_URL,
  );

  const searchParams = request.nextUrl.searchParams;

  searchParams.forEach((value, key) => {
    targetUrl.searchParams.set(key, value);
  });

  const headers = new Headers(request.headers);

  headers.delete("host");

  const body =
    request.method === "GET" ||
    request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
    redirect: "manual",
  });

  const responseHeaders = new Headers(response.headers);

  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(
    response.body,
    {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    },
  );
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;