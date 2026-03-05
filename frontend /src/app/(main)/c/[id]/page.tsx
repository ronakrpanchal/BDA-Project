import React from "react";
import ChatInput from "@/features/chat/components/chat-input";
import MessageBubble from "@/features/chat/components/message-bubble";

type Props = {};

export default function Page({}: Props) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex-grow overflow-y-auto py-4">
        <div className="max-w-2xl mx-auto">
          <MessageBubble isUser={false} />
        </div>
      </div>

    </div>
  );
}
