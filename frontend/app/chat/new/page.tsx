"use client";

import { ChatPanel } from "../../../components/chat/ChatPanel";

export default function NewChatPage() {
  return (
    <div className="flex flex-1 flex-col">
      <ChatPanel conversationId={null} />
    </div>
  );
}

