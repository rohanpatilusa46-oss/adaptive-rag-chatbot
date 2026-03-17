"use client";

import { useParams } from "next/navigation";
import { ChatPanel } from "../../../components/chat/ChatPanel";

export default function ConversationPage() {
  const params = useParams<{ conversationId: string }>();

  return (
    <div className="flex flex-1 flex-col">
      <ChatPanel conversationId={params.conversationId} />
    </div>
  );
}

