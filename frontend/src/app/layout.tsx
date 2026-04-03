import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { OnboardingProvider } from "@/components/onboarding-provider";
import localFont from "next/font/local";
import "./globals.css";

const satoshifont = localFont({
  src: "../../public/fonts/Satoshi-Regular.woff2",
  display: "swap",
  variable: "--font-satoshi",
});
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PlanMyDiet",
  description: "PlanMyDiet your personal AI Diet assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${satoshifont.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <OnboardingProvider>{children}</OnboardingProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
