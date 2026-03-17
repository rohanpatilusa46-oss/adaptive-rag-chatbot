export type Role = "user" | "assistant" | "system" | "tool";

export type Citation = {
  title: string;
  url: string;
  snippet?: string | null;
};

export type ChatMessage = {
  id?: string;
  role: Role;
  content: string;
  citations?: Citation[] | null;
};

export type ChatRequest = {
  user_id?: string | null;
  conversation_id?: string | null;
  message: string;
  stream?: boolean;
};

export type ChatResponse = {
  conversation_id: string;
  message: ChatMessage;
};

