export type UserGender = "male" | "female" | "other";

export interface UserProfile {
  height: number;
  weight: number;
  age: number;
  gender: UserGender;
  bfp: number;
}

export interface UserSession {
  id: number;
  name: string;
  email: string;
  isLoggedIn: boolean;
  onboardingComplete: boolean;
  profile?: UserProfile;
}

const SESSION_KEY = "pmd_session_v1";

export function getStoredSession(): UserSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as UserSession;
  } catch {
    return null;
  }
}

export function setStoredSession(session: UserSession): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearStoredSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(SESSION_KEY);
}

export function getCurrentUserId(): number {
  const session = getStoredSession();
  return session?.id ?? 1;
}
