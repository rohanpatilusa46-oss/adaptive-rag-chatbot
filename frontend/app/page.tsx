"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="max-w-xl px-6 py-10 text-center bg-slate-900/70 rounded-2xl border border-slate-800 shadow-xl">
        <h1 className="text-3xl font-semibold mb-3">Live AI Assistant</h1>
        <p className="text-slate-300 mb-6">
          Ask questions, browse the web when needed, and remember your preferences.
        </p>
        <div className="space-y-4">
          <Link
            href="/chat/new"
            className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            Start a new conversation
          </Link>
          <div className="text-left text-sm text-slate-400 mt-4">
            <p className="font-medium mb-1">Try prompts like:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>“Summarize the latest news about large language models.”</li>
              <li>“Remember that I prefer remote jobs in Europe.”</li>
              <li>“What do you remember about my job preferences?”</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

