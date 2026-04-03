"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronRight, ChevronLeft, ShieldCheck, X } from "lucide-react";
import GoogleSignInButton from "@/components/google-signin-button";
import {
  getStoredSession,
  setStoredSession,
  type UserGender,
  type UserSession,
} from "@/lib/session";
import { getSupabaseBrowserClient } from "@/lib/supabase-client";

type OnboardingContextType = {
  openOnboarding: () => void;
  session: UserSession | null;
};

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

type AuthMode = "login" | "signup";
type FieldKey = "height" | "weight" | "age" | "gender" | "bfp";
type FieldErrors = Partial<Record<FieldKey, string>>;
type AuthUserResponse = {
  user: {
    id: number;
    name: string;
    email: string;
    height?: number | null;
    weight?: number | null;
    age?: number | null;
    gender?: UserGender | null;
    bfp?: number | null;
  };
  profile_complete: boolean;
};

function buildProfileFromResponse(data: AuthUserResponse): UserSession["profile"] {
  const u = data.user;
  if (
    u.height == null ||
    u.weight == null ||
    u.age == null ||
    u.gender == null ||
    u.bfp == null
  ) {
    return undefined;
  }

  return {
    height: Number(u.height),
    weight: Number(u.weight),
    age: Number(u.age),
    gender: u.gender,
    bfp: Number(u.bfp),
  };
}
const GENDER_OPTIONS: Array<{ value: UserGender; label: string; note: string }> = [
  { value: "male", label: "Male", note: "Physiology baseline" },
  { value: "female", label: "Female", note: "Hormonal baseline" },
  { value: "other", label: "Other", note: "Custom profile" },
];

function prefillProfileFromSession(
  stored: UserSession | null,
  setters: {
    setHeight: (value: string) => void;
    setWeight: (value: string) => void;
    setAge: (value: string) => void;
    setGender: (value: UserGender | "") => void;
    setBfp: (value: string) => void;
  }
) {
  if (!stored?.profile) {
    return;
  }

  setters.setHeight(String(stored.profile.height));
  setters.setWeight(String(stored.profile.weight));
  setters.setAge(String(stored.profile.age));
  setters.setGender(stored.profile.gender);
  setters.setBfp(String(stored.profile.bfp));
}

function parsePositiveNumber(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

const STEP_TITLES = [
  "Google Sign-In",
  "Body Metrics",
  "Fitness Profile",
  "Review & Finish",
];

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [session, setSession] = useState<UserSession | null>(null);
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [authMode, setAuthMode] = useState<AuthMode>("signup");

  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState<UserGender | "">("");
  const [bfp, setBfp] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const stored = getStoredSession();
    if (!stored) {
      return;
    }

    setSession(stored);
    prefillProfileFromSession(stored, {
      setHeight,
      setWeight,
      setAge,
      setGender,
      setBfp,
    });
  }, []);

  useEffect(() => {
    const onboardingMode = searchParams.get("onboarding");
    if (onboardingMode !== "profile") {
      return;
    }

    const stored = getStoredSession();
    if (!stored || stored.onboardingComplete) {
      return;
    }

    setSession(stored);
    prefillProfileFromSession(stored, {
      setHeight,
      setWeight,
      setAge,
      setGender,
      setBfp,
    });
    setStep(1);
    setError(null);
    setFieldErrors({});
    setOpen(true);
  }, [searchParams]);

  const resetWizard = () => {
    setStep(0);
    setError(null);
    setFieldErrors({});
    setAuthMode("signup");
    setHeight("");
    setWeight("");
    setAge("");
    setGender("");
    setBfp("");
  };

  const closeWizard = () => {
    setOpen(false);
    setError(null);
    setFieldErrors({});
  };

  const openOnboarding = () => {
    const stored = getStoredSession();

    if (stored?.isLoggedIn && stored.onboardingComplete) {
      router.push(`/c/${stored.id}`);
      return;
    }

    if (stored) {
      setSession(stored);
      prefillProfileFromSession(stored, {
        setHeight,
        setWeight,
        setAge,
        setGender,
        setBfp,
      });
      setStep(stored.onboardingComplete ? 0 : 1);
    } else {
      setStep(0);
    }

    setError(null);
    setFieldErrors({});
    setOpen(true);
  };

  const handleGoogleCredential = async (credential: string) => {
    setBusy(true);
    setError(null);

    try {
      const supabase = getSupabaseBrowserClient();
      if (!supabase) {
        throw new Error(
          "Supabase frontend env is missing. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
        );
      }

      const { data: signInData, error: signInError } = await supabase.auth.signInWithIdToken({
        provider: "google",
        token: credential,
      });

      if (signInError) {
        throw signInError;
      }

      const signedInUser = signInData.user;
      if (!signedInUser?.email) {
        throw new Error("Google account email is unavailable.");
      }

      const displayName =
        (signedInUser.user_metadata?.full_name as string | undefined) ||
        (signedInUser.user_metadata?.name as string | undefined) ||
        signedInUser.email.split("@")[0];

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: displayName,
          email: signedInUser.email,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to connect Google account to your profile.");
      }

      const data: AuthUserResponse = await response.json();
      const nextSession: UserSession = {
        id: data.user.id,
        name: data.user.name,
        email: data.user.email,
        isLoggedIn: true,
        onboardingComplete: data.profile_complete,
        profile: buildProfileFromResponse(data),
      };

      setStoredSession(nextSession);
      setSession(nextSession);

      if (data.profile_complete) {
        closeWizard();
        router.push(`/c/${data.user.id}`);
        return;
      }

      prefillProfileFromSession(nextSession, {
        setHeight,
        setWeight,
        setAge,
        setGender,
        setBfp,
      });
      setStep(1);
      setFieldErrors({});
      setError(null);
      setOpen(true);

      if (searchParams.get("onboarding") === "profile") {
        router.replace("/");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const goNextFromStepOne = () => {
    const nextErrors: FieldErrors = {};
    const parsedHeight = parsePositiveNumber(height);
    const parsedWeight = parsePositiveNumber(weight);

    if (!parsedHeight) {
      nextErrors.height = "Please enter a valid height.";
    }

    if (!parsedWeight) {
      nextErrors.weight = "Please enter a valid weight.";
    }

    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      setError("Please fix the highlighted fields to continue.");
      return;
    }

    setError(null);
    setStep(2);
  };

  const goNextFromStepTwo = () => {
    const nextErrors: FieldErrors = {};
    const parsedAge = parsePositiveNumber(age);
    const parsedBfp = parsePositiveNumber(bfp);

    if (!parsedAge || parsedAge > 120) {
      nextErrors.age = "Enter an age between 1 and 120.";
    }

    if (!gender) {
      nextErrors.gender = "Please select your gender.";
    }

    if (!parsedBfp || parsedBfp > 100) {
      nextErrors.bfp = "Enter body fat percentage between 1 and 100.";
    }

    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      setError("Please fix the highlighted fields to continue.");
      return;
    }

    setError(null);
    setStep(3);
  };

  const completeOnboarding = async () => {
    const activeSession = session ?? getStoredSession();
    if (!activeSession?.id || !gender) {
      setError("Session expired. Please login again.");
      setStep(0);
      return;
    }

    const parsedHeight = parsePositiveNumber(height);
    const parsedWeight = parsePositiveNumber(weight);
    const parsedAge = parsePositiveNumber(age);
    const parsedBfp = parsePositiveNumber(bfp);

    if (!parsedHeight || !parsedWeight || !parsedAge || !parsedBfp) {
      setError("Some values are invalid. Please review your profile details.");
      return;
    }

    setBusy(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user/profile`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: activeSession.id,
          height: parsedHeight,
          weight: parsedWeight,
          age: Math.round(parsedAge),
          gender,
          bfp: parsedBfp,
        }),
      });

      if (!response.ok) {
        throw new Error("Could not save your profile. Please try again.");
      }

      const nextSession: UserSession = {
        ...activeSession,
        onboardingComplete: true,
        profile: {
          height: parsedHeight,
          weight: parsedWeight,
          age: Math.round(parsedAge),
          gender,
          bfp: parsedBfp,
        },
      };

      setStoredSession(nextSession);
      setSession(nextSession);
      closeWizard();
      router.push(`/c/${activeSession.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const value = useMemo(
    () => ({
      openOnboarding,
      session,
    }),
    [session]
  );

  const progress = ((step + 1) / 4) * 100;

  return (
    <OnboardingContext.Provider value={value}>
      {children}
      {open && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 px-4 py-8">
          <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-slate-700 bg-[#0a1020] text-white shadow-[0_20px_80px_rgba(0,0,0,0.55)]">
            <div className="pointer-events-none absolute -top-28 left-0 h-80 w-80 rounded-full bg-cyan-500/20 blur-3xl" />
            <div className="pointer-events-none absolute -right-20 bottom-0 h-80 w-80 rounded-full bg-indigo-600/20 blur-3xl" />

            <div className="relative z-10 border-b border-slate-700/80 px-6 py-5 sm:px-8">
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-cyan-300/90">PlanMyDiet Onboarding</p>
                  <h2 className="mt-1 text-2xl font-semibold">{STEP_TITLES[step]}</h2>
                </div>
                <button
                  onClick={closeWizard}
                  className="rounded-lg border border-slate-600 p-2 text-slate-300 transition hover:bg-white/10"
                  aria-label="Close onboarding"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="mb-3 h-2 w-full overflow-hidden rounded-full bg-slate-700">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-indigo-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <div className="grid grid-cols-4 gap-2">
                {STEP_TITLES.map((title, index) => (
                  <div key={title} className="flex items-center gap-2">
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold ${
                        index <= step ? "bg-cyan-400 text-slate-950" : "bg-slate-700 text-slate-300"
                      }`}
                    >
                      {index + 1}
                    </span>
                    <span className="hidden text-xs text-slate-300 sm:inline">{title}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative z-10 space-y-5 px-6 py-6 sm:px-8">
              {step === 0 && (
                <div className="space-y-5">
                  <div className="inline-flex rounded-xl border border-slate-600 bg-slate-900/70 p-1">
                    <button
                      onClick={() => setAuthMode("signup")}
                      className={`rounded-lg px-4 py-2 text-sm transition ${
                        authMode === "signup" ? "bg-cyan-500 text-slate-950" : "text-slate-300"
                      }`}
                    >
                      Sign up
                    </button>
                    <button
                      onClick={() => setAuthMode("login")}
                      className={`rounded-lg px-4 py-2 text-sm transition ${
                        authMode === "login" ? "bg-cyan-500 text-slate-950" : "text-slate-300"
                      }`}
                    >
                      Login
                    </button>
                  </div>

                  <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
                    <p className="text-sm text-slate-200">
                      {authMode === "signup"
                        ? "Create your account with Google and we will set up your personalized health profile in a few steps."
                        : "Sign in with Google. If your profile is already complete, we will take you straight to chat."}
                    </p>
                    <p className="mt-2 flex items-center gap-2 text-xs text-cyan-200/90">
                      <ShieldCheck size={14} />
                      Secure OAuth sign-in powered by Google and Supabase
                    </p>
                  </div>

                  <GoogleSignInButton
                    mode={authMode}
                    disabled={busy}
                    onCredential={handleGoogleCredential}
                  />

                  {busy && (
                    <p className="text-center text-xs text-slate-300">Signing you in...</p>
                  )}
                </div>
              )}

              {step === 1 && (
                <div className="space-y-5">
                  <p className="text-sm text-slate-300">Step 1 of profile setup: add your body measurements.</p>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm text-slate-300">Height (cm)</label>
                      <Input
                        type="number"
                        value={height}
                        onChange={(e) => {
                          setHeight(e.target.value);
                          setFieldErrors((prev) => ({ ...prev, height: undefined }));
                        }}
                        className="h-11 border-slate-600 bg-slate-900/50"
                      />
                      {fieldErrors.height && <p className="text-xs text-rose-300">{fieldErrors.height}</p>}
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm text-slate-300">Weight (kg)</label>
                      <Input
                        type="number"
                        value={weight}
                        onChange={(e) => {
                          setWeight(e.target.value);
                          setFieldErrors((prev) => ({ ...prev, weight: undefined }));
                        }}
                        className="h-11 border-slate-600 bg-slate-900/50"
                      />
                      {fieldErrors.weight && <p className="text-xs text-rose-300">{fieldErrors.weight}</p>}
                    </div>
                  </div>

                  <div className="flex justify-between">
                    <Button variant="outline" onClick={() => setStep(0)} className="border-slate-600 text-white hover:bg-white/10">
                      <ChevronLeft className="mr-2" size={16} />
                      Back
                    </Button>
                    <Button onClick={goNextFromStepOne} className="bg-cyan-500 text-slate-950 hover:bg-cyan-400">
                      Continue
                      <ChevronRight className="ml-2" size={16} />
                    </Button>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-5">
                  <p className="text-sm text-slate-300">Step 2 of profile setup: add your fitness profile.</p>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm text-slate-300">Age</label>
                      <Input
                        type="number"
                        value={age}
                        onChange={(e) => {
                          setAge(e.target.value);
                          setFieldErrors((prev) => ({ ...prev, age: undefined }));
                        }}
                        className="h-11 border-slate-600 bg-slate-900/50"
                      />
                      {fieldErrors.age && <p className="text-xs text-rose-300">{fieldErrors.age}</p>}
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm text-slate-300">Body Fat %</label>
                      <Input
                        type="number"
                        value={bfp}
                        onChange={(e) => {
                          setBfp(e.target.value);
                          setFieldErrors((prev) => ({ ...prev, bfp: undefined }));
                        }}
                        className="h-11 border-slate-600 bg-slate-900/50"
                      />
                      {fieldErrors.bfp && <p className="text-xs text-rose-300">{fieldErrors.bfp}</p>}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-300">Gender</label>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                      {GENDER_OPTIONS.map((option) => {
                        const active = gender === option.value;
                        return (
                          <button
                            type="button"
                            key={option.value}
                            onClick={() => {
                              setGender(option.value);
                              setFieldErrors((prev) => ({ ...prev, gender: undefined }));
                            }}
                            className={`rounded-xl border p-3 text-left transition ${
                              active
                                ? "border-cyan-400 bg-cyan-400/15 text-cyan-100"
                                : "border-slate-600 bg-slate-900/50 text-slate-200 hover:border-slate-500"
                            }`}
                          >
                            <p className="text-sm font-semibold">{option.label}</p>
                            <p className="text-xs text-slate-400">{option.note}</p>
                          </button>
                        );
                      })}
                    </div>
                    {fieldErrors.gender && <p className="text-xs text-rose-300">{fieldErrors.gender}</p>}
                  </div>

                  <div className="flex justify-between">
                    <Button variant="outline" onClick={() => setStep(1)} className="border-slate-600 text-white hover:bg-white/10">
                      <ChevronLeft className="mr-2" size={16} />
                      Back
                    </Button>
                    <Button onClick={goNextFromStepTwo} className="bg-cyan-500 text-slate-950 hover:bg-cyan-400">
                      Continue
                      <ChevronRight className="ml-2" size={16} />
                    </Button>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="space-y-5">
                  <p className="text-sm text-slate-300">Review your profile. You can go back and edit any field.</p>
                  <div className="grid grid-cols-1 gap-3 rounded-2xl border border-slate-700 bg-slate-900/60 p-4 text-sm sm:grid-cols-2">
                    <p><span className="text-slate-400">Name:</span> {session?.name || "-"}</p>
                    <p><span className="text-slate-400">Email:</span> {session?.email || "-"}</p>
                    <p><span className="text-slate-400">Height:</span> {height} cm</p>
                    <p><span className="text-slate-400">Weight:</span> {weight} kg</p>
                    <p><span className="text-slate-400">Age:</span> {age} years</p>
                    <p><span className="text-slate-400">Gender:</span> {gender || "-"}</p>
                    <p><span className="text-slate-400">Body Fat %:</span> {bfp}%</p>
                  </div>

                  <div className="flex justify-between">
                    <Button variant="outline" onClick={() => setStep(2)} className="border-slate-600 text-white hover:bg-white/10">
                      <ChevronLeft className="mr-2" size={16} />
                      Back
                    </Button>
                    <Button onClick={completeOnboarding} disabled={busy} className="bg-cyan-500 text-slate-950 hover:bg-cyan-400">
                      {busy ? "Saving..." : "Finish and Continue"}
                    </Button>
                  </div>
                </div>
              )}

              {error && (
                <p className="rounded-lg border border-rose-400/30 bg-rose-900/20 px-3 py-2 text-sm text-rose-200">
                  {error}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const ctx = useContext(OnboardingContext);
  if (!ctx) {
    throw new Error("useOnboarding must be used within OnboardingProvider");
  }
  return ctx;
}
