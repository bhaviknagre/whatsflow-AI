"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { login } from "@/lib/auth/api";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const response = await login({
        email,
        password,
      });

      sessionStorage.setItem(
        "access_token",
        response.access_token,
      );

      router.push("/inbox");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to sign in",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-6"
      >
        <div>
          <h1 className="text-3xl font-bold">
            Welcome back
          </h1>

          <p className="mt-2 text-muted-foreground">
            Sign in to your WhatsFlow workspace.
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-red-300 p-3 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <label
            htmlFor="email"
            className="text-sm font-medium"
          >
            Email
          </label>

          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            className="w-full rounded-md border p-3"
          />
        </div>

        <div className="space-y-2">
          <label
            htmlFor="password"
            className="text-sm font-medium"
          >
            Password
          </label>

          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            className="w-full rounded-md border p-3"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-black p-3 text-white disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}