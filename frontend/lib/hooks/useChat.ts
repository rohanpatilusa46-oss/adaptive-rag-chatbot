"use client";

import { useState } from "react";
import { sendChat } from "@/lib/api/chat";
import type { ChatMessage } from "@/lib/types/chat";

type UseChatOptions = {
  userId?: string | null;
  conversationId?: string | null;
};

export function useChat(options: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(
    options.conversationId ?? null
  );
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isSending) return;

    setError(null);
    setIsSending(true);

    const tempUserMessage: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      role: "user",
      content
    };

    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const response = await sendChat({
        user_id: options.userId ?? "demo-user",
        conversation_id: conversationId,
        message: content,
        stream: false
      });

      setConversationId(response.conversation_id);

      const assistantMessage = response.message;
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (e) {
      console.error(e);
      setError("Failed to send message. Please try again.");
    } finally {
      setIsSending(false);
    }
  };

  return {
    messages,
    sendMessage,
    isSending,
    error,
    conversationId
  };
}

