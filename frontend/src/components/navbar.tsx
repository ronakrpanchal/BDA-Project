"use client";

import React from "react";
import { Dumbbell } from "lucide-react";
import { Button } from "./ui/button";
import Link from "next/link";
import { Separator } from "./ui/separator";
import { useOnboarding } from "@/components/onboarding-provider";

const navLinks = [
  {
    name: "About",
    href: "/about",
  },
  {
    name: "Features",
    href: "/features",
  },
  {
    name: "Pricing",
    href: "/pricing",
  },
  {
    name: "FAQ's",
    href: "/faq",
  },
];

export default function Navbar() {
  const { openOnboarding } = useOnboarding();

  return (
    <>
      <nav className="wrapper p-5 py-7 flex justify-between items-center">
        <h2 className="flex items-center text-3xl">
          <Dumbbell className="mr-2" />
          PlanMyDiet
        </h2>
        <div className="flex gap-4 items-center">
          {navLinks.map((link) => (
            <Link key={link.href} href={link.href}>
              {link.name}
            </Link>
          ))}
          <Button className="cursor-pointer" onClick={openOnboarding}>
            Get started
          </Button>
        </div>
      </nav>
      <Separator />
    </>
  );
}
