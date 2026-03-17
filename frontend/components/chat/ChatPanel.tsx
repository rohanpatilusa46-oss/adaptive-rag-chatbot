"use client";

import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";
import { useHealth } from "@/lib/hooks/useHealth";
import { useChat } from "@/lib/hooks/useChat";

type Props = {
  conversationId: string | null;
};

export function ChatPanel({ conversationId }: Props) {
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth();

  const {
    messages,
    sendMessage,
    isSending,
    error: chatError
  } = useChat({
    userId: "demo-user",
    conversationId
  });

  return (
    <div className="flex flex-1 flex-col">
      <header className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/70">
        <div className="space-y-0.5">
          <h2 className="text-sm font-medium">
            {conversationId ? "Conversation" : "New conversation"}
          </h2>
          <p className="text-xs text-slate-400">
            Backend status:{" "}
            {healthLoading
              ? "Checking..."
              : healthError
              ? "Unavailable"
              : health?.status === "ok"
              ? `OK (${health.env})`
              : "Unknown"}
          </p>
        </div>
        {chatError && (
          <p className="text-xs text-red-400 max-w-xs text-right">{chatError}</p>
        )}
      </header>
      <div className="flex-1 flex flex-col">
        <MessageList messages={messages} />
        <ChatInput
          onSend={async (content) => {
            await sendMessage(content);
          }}
          disabled={isSending}
        />
      </div>
    </div>
  );
}


