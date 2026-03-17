import type { ChatMessage } from "./ChatPanel";
import classNames from "classnames";

type Props = {
  message: ChatMessage;
};

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const alignment = isUser ? "items-end" : "items-start";
  const bubbleClasses = classNames(
    "max-w-lg rounded-2xl px-4 py-2 text-sm shadow",
    isUser
      ? "bg-accent text-white rounded-br-sm"
      : "bg-slate-800 text-slate-100 rounded-bl-sm"
  );

  return (
    <div className={`flex ${alignment}`}>
      <div className={bubbleClasses}>{message.content}</div>
    </div>
  );
}

