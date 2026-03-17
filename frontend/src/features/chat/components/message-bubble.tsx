"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  SendHorizontal,
  Search,
  Lightbulb,
  MoreHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Markdown from "react-markdown";

// Types
type Message = {
  content: string;
  isUser: boolean;
};

interface ChatComponentProps {
  className?: string;
}

export default function ChatComponent({ className }: ChatComponentProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "44px";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${scrollHeight}px`;
    }
  }, [message]);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!message.trim()) return;
    
    // Add user message to the chat
    const userMessage = { content: message, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    const userQuery = message; // Store message before clearing
    setMessage("");
    setIsLoading(true);
    
    try {
      // Send the message to your API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health_ai`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userQuery,
          user_id: 1
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("first",data)
      
      // Make sure we're handling the response correctly based on your API structure
      const botResponse = data.ai_response?.message || data.message || "Sorry, I couldn't process that request.";

// Add the bot response to the chat
setMessages(prev => [...prev, { 
  content: botResponse, 
  isUser: false 
}]);
    } catch (error) {
      console.error("Error sending message:", error);
      // Add error message
      setMessages(prev => [...prev, { 
        content: "I'm having trouble connecting to the server. Please check your connection and try again.", 
        isUser: false 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={cn("flex flex-col h-screen", className)}>
      {/* Messages container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Start a conversation with PlanMyDiet
          </div>
        ) : (
          messages.map((msg, index) => (
            <MessageBubble key={index} isUser={msg.isUser} content={msg.content} />
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-500/10 p-3 rounded-xl animate-pulse text-gray-400">
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input container */}
      <div className="p-4 border-t border-gray-800/50">
        <div className="rounded-2xl overflow-hidden transition-all duration-300 border bg-gray-500/10">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            className="w-full bg-transparent border-0 min-h-14 max-h-[300px] px-5 py-4 text-white focus:outline-none placeholder:text-gray-500 resize-none"
            rows={1}
          />

          {/* Bottom action bar */}
          <div className="flex items-center justify-between px-5 py-3 border-t border-gray-800/50">
            {/* Left side buttons */}
            <div className="flex items-center space-x-3">
              <button className="w-9 h-9 flex items-center justify-center text-gray-400 hover:text-indigo-400 rounded-full hover:bg-white/5 transition-colors">
                <Search size={18} />
              </button>
              <button className="w-9 h-9 flex items-center justify-center text-gray-400 hover:text-indigo-400 rounded-full hover:bg-white/5 transition-colors">
                <Lightbulb size={18} />
              </button>
              <button className="w-9 h-9 flex items-center justify-center text-gray-400 hover:text-indigo-400 rounded-full hover:bg-white/5 transition-colors">
                <MoreHorizontal size={18} />
              </button>
            </div>
            {/* Right side send button */}
            <button
              onClick={handleSendMessage}
              disabled={!message.trim() || isLoading}
              className={`px-5 h-10 flex items-center justify-center rounded-full text-white duration-200 ${
                message.trim() && !isLoading
                  ? "bg-indigo-600 shadow-md hover:bg-indigo-700"
                  : "bg-transparent border border-gray-700 text-gray-500"
              }`}
            >
              <SendHorizontal size={18} className="mr-2" />
              <span className="text-sm font-medium">Send</span>
            </button>
          </div>
        </div>
        <div className="text-xs text-center mt-2 text-gray-500">
          PlanMyDiet is designed to help you achieve your daily goals
        </div>
      </div>
    </div>
  );
}

// Message bubble component
type MessageBubbleProps = {
  isUser: boolean;
  content: string;
};

function MessageBubble({ isUser, content }: MessageBubbleProps) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div 
        className={`max-w-lg p-3 rounded-xl shadow-md ${
          isUser 
            ? 'bg-indigo-600 text-white' 
            : 'bg-gray-500/10 border border-gray-800/50 text-white'
        }`}
      >
        {isUser ? (
  <div>{content}</div>
) : (
  <Markdown>
    {content}
  </Markdown>
)}
      </div>
    </div>
  );
}