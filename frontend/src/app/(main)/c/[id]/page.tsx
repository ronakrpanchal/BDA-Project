import MessageBubble from "@/features/chat/components/message-bubble";

export default function Page() {
  return (
    <div className="flex h-full flex-col">
      <div className="flex-grow overflow-y-auto py-4">
        <div className="max-w-2xl mx-auto">
          <MessageBubble />
        </div>
      </div>
    </div>
  );
}
