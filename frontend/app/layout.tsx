import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/shell/Sidebar";
import { Header } from "@/components/shell/Header";

export const metadata: Metadata = {
  title: "SupeRR Intelligence — Rajasthan Royals Cricket Scouting & Auction Intelligence",
  description:
    "Evidence-first cricket analytics and auction intelligence platform inspired by Rajasthan Royals.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen bg-slate-50 font-sans text-slate-800 antialiased selection:bg-pink-100 selection:text-rr-pink">
        <Sidebar />
        <div className="flex-1 flex flex-col min-h-screen overflow-x-clip">
          <Header />
          <main className="flex-1 px-8 pt-5 pb-8">
            <div className="max-w-7xl mx-auto space-y-5">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
