import "./globals.css";
import type { ReactNode } from "react";
import { Sidebar } from "../components/sidebar/Sidebar";

export const metadata = {
  title: "Live AI Assistant",
  description: "Real-time AI assistant with search and memory"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-white">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 flex flex-col bg-slate-900/60">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

