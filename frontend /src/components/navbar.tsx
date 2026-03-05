import React from "react";
import { Dumbbell } from "lucide-react";
import { Button } from "./ui/button";
import Link from "next/link";
import { Separator } from "./ui/separator";
import { GiGymBag } from "react-icons/gi";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

type Props = {};

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

export default function Navbar({}: Props) {
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

<Link href="/c/id">
  <Button className="cursor-pointer">Get started</Button>
</Link>        </div>
      </nav>
      <Separator />
    </>
  );
}
