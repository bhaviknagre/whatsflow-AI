"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { register } from "@/lib/auth/api";

export default function RegisterPage() {
  const router = useRouter();

  const [organizationName, setOrganizationName] =
    useState("");
  const [fullName, setFullName] = useState("");
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
      const response = await register({
        organization_name: organizationName,
        full_name: fullName,
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
          : "Unable to create account",
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
            Create your workspace
          </h1>

          <p className="mt-2 text-muted-foreground">
            Set up WhatsFlow for your business.
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-red-300 p-3 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <label
            htmlFor="organizationName"
            className="text-sm font-medium"
          >
            Business name
          </label>

          <input
            id="organizationName"
            type="text"
            required
            minLength={2}
            value={organizationName}
            onChange={(event) =>
              setOrganizationName(event.target.value)
            }
            className="w-full rounded-md border p-3"
          />
        </div>

        <div className="space-y-2">
          <label
            htmlFor="fullName"
            className="text-sm font-medium"
          >
            Your name
          </label>

          <input
            id="fullName"
            type="text"
            required
            minLength={2}
            value={fullName}
            onChange={(event) =>
              setFullName(event.target.value)
            }
            className="w-full rounded-md border p-3"
          />
        </div>

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
            minLength={8}
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            className="w-full rounded-md border p-3"
          />

          <p className="text-xs text-muted-foreground">
            At least 8 characters.
          </p>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-black p-3 text-white disabled:opacity-50"
        >
          {loading
            ? "Creating account..."
            : "Create account"}
        </button>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-foreground underline"
          >
            Sign in
          </Link>
        </p>
      </form>
    </main>
  );
}
