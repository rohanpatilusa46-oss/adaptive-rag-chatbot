import type { ChatMessage } from "./ChatPanel";
import { MessageBubble } from "@/components/chat/MessageBubble";

type Props = {
  messages: ChatMessage[];
};

export function MessageList({ messages }: Props) {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center text-sm text-slate-400">
          Start typing to begin a conversation.
        </div>
      ) : (
        messages.map((m) => <MessageBubble key={m.id} message={m} />)
      )}
    </div>
  );
}

