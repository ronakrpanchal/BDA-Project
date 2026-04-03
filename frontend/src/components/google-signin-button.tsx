"use client";

import { useEffect, useRef } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential?: string }) => void;
          }) => void;
          renderButton: (
            element: HTMLElement,
            options: {
              theme?: "outline" | "filled_blue" | "filled_black";
              size?: "large" | "medium" | "small";
              type?: "standard" | "icon";
              shape?: "rectangular" | "pill" | "circle" | "square";
              text?: "signin_with" | "signup_with" | "continue_with" | "signin";
              logo_alignment?: "left" | "center";
              width?: string;
            }
          ) => void;
        };
      };
    };
  }
}

type GoogleSignInButtonProps = {
  onCredential: (credential: string) => void;
  mode: "login" | "signup";
  disabled?: boolean;
  clientId?: string;
};

const SCRIPT_ID = "google-identity-services";

export default function GoogleSignInButton({
  onCredential,
  mode,
  disabled = false,
  clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
}: GoogleSignInButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!clientId || disabled) {
      return;
    }

    const render = () => {
      if (!window.google || !containerRef.current) {
        return;
      }

      containerRef.current.innerHTML = "";

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          if (response.credential) {
            onCredential(response.credential);
          }
        },
      });

      window.google.accounts.id.renderButton(containerRef.current, {
        theme: "outline",
        size: "large",
        type: "standard",
        shape: "pill",
        text: mode === "signup" ? "signup_with" : "signin_with",
        logo_alignment: "left",
        width: "360",
      });
    };

    const existingScript = document.getElementById(SCRIPT_ID);
    if (existingScript) {
      render();
      return;
    }

    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = render;
    document.head.appendChild(script);
  }, [clientId, mode, disabled, onCredential]);

  if (!clientId) {
    return (
      <p className="rounded-lg border border-amber-400/30 bg-amber-900/20 px-3 py-2 text-sm text-amber-200">
        Missing NEXT_PUBLIC_GOOGLE_CLIENT_ID in frontend env.
      </p>
    );
  }

  return (
    <div className="flex w-full justify-center">
      <div className="g_id_signin" ref={containerRef} aria-disabled={disabled} />
    </div>
  );
}
