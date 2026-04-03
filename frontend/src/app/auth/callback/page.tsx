"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getSupabaseBrowserClient } from "@/lib/supabase-client";
import { setStoredSession, type UserSession } from "@/lib/session";

type AuthUserResponse = {
  user: {
    id: number;
    name: string;
    email: string;
    height?: number | null;
    weight?: number | null;
    age?: number | null;
    gender?: "male" | "female" | "other" | null;
    bfp?: number | null;
  };
  profile_complete: boolean;
};

function buildProfile(data: AuthUserResponse): UserSession["profile"] {
  const user = data.user;
  if (
    user.height == null ||
    user.weight == null ||
    user.age == null ||
    user.gender == null ||
    user.bfp == null
  ) {
    return undefined;
  }

  return {
    height: Number(user.height),
    weight: Number(user.weight),
    age: Number(user.age),
    gender: user.gender,
    bfp: Number(user.bfp),
  };
}

function CallbackPendingState() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0f1118] p-6 text-white">
      <div className="w-full max-w-md rounded-2xl border border-indigo-500/30 bg-black/30 p-6 text-center">
        <h1 className="text-xl font-semibold">Finalizing Google Sign-In</h1>
        <p className="mt-2 text-sm text-gray-300">Please wait while we prepare your account.</p>
      </div>
    </div>
  );
}

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const providerError = searchParams.get("error_description") || searchParams.get("error");
        if (providerError) {
          throw new Error(providerError);
        }

        const code = searchParams.get("code");
        const supabase = getSupabaseBrowserClient();

        if (!supabase) {
          throw new Error("Supabase client is not configured in frontend env.");
        }

        if (code) {
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) {
            throw exchangeError;
          }
        }

        const {
          data: { user },
          error: userError,
        } = await supabase.auth.getUser();

        if (userError) {
          throw userError;
        }

        if (!user?.email) {
          throw new Error("Google account email is unavailable.");
        }

        const displayName =
          (user.user_metadata?.full_name as string | undefined) ||
          (user.user_metadata?.name as string | undefined) ||
          user.email.split("@")[0];

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: displayName,
            email: user.email,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to connect account to backend user profile.");
        }

        const data: AuthUserResponse = await response.json();
        const session: UserSession = {
          id: data.user.id,
          name: data.user.name,
          email: data.user.email,
          isLoggedIn: true,
          onboardingComplete: data.profile_complete,
          profile: buildProfile(data),
        };

        setStoredSession(session);

        if (data.profile_complete) {
          router.replace(`/c/${data.user.id}`);
        } else {
          router.replace("/?onboarding=profile");
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Google sign-in failed.";
        setError(message);
      }
    };

    void run();
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0f1118] p-6 text-white">
      <div className="w-full max-w-md rounded-2xl border border-indigo-500/30 bg-black/30 p-6 text-center">
        {!error ? (
          <>
            <h1 className="text-xl font-semibold">Finalizing Google Sign-In</h1>
            <p className="mt-2 text-sm text-gray-300">Please wait while we prepare your account.</p>
          </>
        ) : (
          <>
            <h1 className="text-xl font-semibold text-red-400">Sign-In Error</h1>
            <p className="mt-2 text-sm text-gray-200">{error}</p>
            <button
              className="mt-5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-700"
              onClick={() => router.replace("/")}
            >
              Back to Home
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<CallbackPendingState />}>
      <AuthCallbackContent />
    </Suspense>
  );
}
