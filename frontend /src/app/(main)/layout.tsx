import SideBar from "@/components/sidebar";
import React from "react";

type Props = { children: React.ReactNode };

export default function Layout({ children }: Props) {
  return (
    <div className="flex h-screen bg-[#0e0e10]">
      <SideBar />
      <main className="flex-1 overflow-x-auto">
        <div className="max-w-[1500px] mx-auto h-screen pt-16">{children}</div>
      </main>
    </div>
  );
}
