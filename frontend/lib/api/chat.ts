import { apiRequest } from "@/lib/api/client";
import type { ChatRequest, ChatResponse } from "@/lib/types/chat";

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: request
  });
}

