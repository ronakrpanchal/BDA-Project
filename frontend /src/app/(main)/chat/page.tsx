import React from "react";
import ChatInput from "@/features/chat/components/chat-input";

type Props = {};

export default function Page({}: Props) {
  return (
    <div className="flex justify-center items-center h-full flex-col gap-5">
      <div className="text-center mb-4">
        <h2 className="text-5xl font-bold">Welcome to PlanMyDiet 👋</h2>
        <h2 className="text-2xl mt-2">What can I help you with?</h2>
      </div>
      <ChatInput />
    </div>
  );
}
