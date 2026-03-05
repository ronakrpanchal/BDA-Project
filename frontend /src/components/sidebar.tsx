"use client";

import React from "react";
import { Utensils, MessageCircle, Trophy, NotebookPen } from "lucide-react";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";

type Props = {};

const Links = [
  { name: "Chat", href: "/c/id", icon: MessageCircle, optional: "/c" },
  { name: "Diets", href: "/diet", icon: Utensils },
  { name: "Achievement", href: "/achievement", icon: Trophy },
  { name: "Notes", href: "/notes", icon: NotebookPen },
];

export default function SideBar({}: Props) {
  const activeLink = usePathname();

  return (
    <motion.aside
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="h-screen flex flex-col w-64 bg-black/30 border-r border-gray-800/30 backdrop-blur-md"
    >
      {/* Logo */}
      <div className="p-6">
        <h2 className="text-2xl font-bold items-center flex gap-2 text-white">
          <Utensils className="text-indigo-400" />
          <span>PlanMyDiet</span>
        </h2>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto py-6 px-4">
        <nav className="flex flex-col gap-2">
          {Links.map((item) => (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`flex items-center text-sm rounded-xl cursor-pointer py-3 px-4 font-medium transition-all duration-300 ${
                  activeLink === item.href ||
                  activeLink.startsWith(item.optional || "/x")
                    ? "bg-gradient-to-r from-indigo-600/50 to-indigo-500/30 text-white shadow-lg border-l-4 border-indigo-400"
                    : "text-gray-300 hover:bg-white/10"
                }`}
              >
                <item.icon
                  size={20}
                  className={`${
                    activeLink === item.href
                      ? "text-indigo-300"
                      : "text-gray-400"
                  }`}
                />
                <span className="ml-3">{item.name}</span>
                {activeLink === item.href && (
                  <motion.div
                    layoutId="sidebar"
                    className="ml-auto w-1.5 h-1.5 bg-indigo-400 rounded-full"
                  ></motion.div>
                )}
              </motion.div>
            </Link>
          ))}
        </nav>
      </div>

      {/* User Profile */}
      <motion.div transition={{ duration: 0.2 }} className="p-4">
        <div className="flex items-center space-x-3 bg-white/5 p-3 rounded-xl cursor-pointer hover:bg-white/15 transition-all duration-300 border border-indigo-500/20">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-full flex items-center justify-center text-xs font-medium text-white">
            JD
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">John Doe</p>
            <p className="text-xs text-indigo-200/70">Pro Member</p>
          </div>
        </div>
      </motion.div>
    </motion.aside>
  );
}
