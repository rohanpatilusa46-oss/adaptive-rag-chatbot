"use client";

import { useState, KeyboardEvent } from "react";

type Props = {
  onSend: (content: string) => Promise<void> | void;
  disabled?: boolean;
};

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    if (!value.trim() || isSending || disabled) return;
    setIsSending(true);
    try {
      await onSend(value.trim());
      setValue("");
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="border-t border-slate-800 bg-slate-900/80 px-4 py-3">
      <div className="flex items-end gap-2">
        <textarea
          className="flex-1 resize-none rounded-xl border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          rows={1}
          placeholder="Ask anything..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          type="button"
          className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-accent text-sm font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
          onClick={() => void handleSend()}
          disabled={disabled || isSending || !value.trim()}
          aria-label="Send message"
        >
          →
        </button>
      </div>
    </div>
  );
}

