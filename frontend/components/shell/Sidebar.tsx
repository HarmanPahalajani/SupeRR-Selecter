"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  Compass,
  Users,
  GitCompare,
  Layers,
  Gavel,
  BookmarkCheck,
  BookOpen,
  UserCheck,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  exact?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "INTELLIGENCE",
    items: [
      { name: "Intelligence Overview", href: "/", icon: Compass, exact: true },
      { name: "Player Discovery", href: "/discovery", icon: Users },
      { name: "Player Intelligence", href: "/players/47", icon: UserCheck },
      { name: "Player Comparison Lab", href: "/comparison", icon: GitCompare },
    ],
  },
  {
    title: "RECRUITMENT",
    items: [
      { name: "Squad Architect", href: "/squad-architect", icon: Layers },
      { name: "Auction Decision Simulator", href: "/auction-simulator", icon: Gavel },
      { name: "Scouting Watchlist", href: "/watchlist", icon: BookmarkCheck },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      { name: "Methodology & Validation", href: "/methodology", icon: BookOpen },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between h-screen sticky top-0 shrink-0 z-40 select-none shadow-sm">
      <div className="overflow-y-auto">
        {/* Brand Header */}
        <div className="px-5 py-4 border-b border-slate-200 bg-white">
          <Link href="/" className="flex items-center gap-3 group">
            {/* Official RR Crest Container */}
            <div className="relative w-11 h-11 shrink-0 flex items-center justify-center bg-white p-0.5 rounded-lg border border-slate-100 shadow-sm group-hover:border-pink-200 transition-colors">
              <img
                src="/images/rr-logo.png"
                alt="Rajasthan Royals Crest"
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <div className="font-bold text-sm tracking-tight text-rr-navy flex items-center gap-1.5 group-hover:text-rr-pink transition-colors">
                <span>SupeRR</span>
                <span className="text-rr-pink font-extrabold">Intelligence</span>
              </div>
              <div className="text-[10px] text-slate-500 font-medium">
                Cricket Scouting & Auction Intelligence
              </div>
            </div>
          </Link>
        </div>

        {/* Navigation Sections */}
        <div className="p-3 space-y-5">
          {NAV_SECTIONS.map((section) => (
            <div key={section.title} className="space-y-1">
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 tracking-wider uppercase">
                {section.title}
              </div>
              <nav className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = item.exact
                    ? pathname === item.href
                    : pathname.startsWith(item.href);

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? "bg-pink-50 text-rr-navy font-semibold border-l-4 border-rr-pink shadow-xs"
                          : "text-slate-600 hover:text-rr-navy hover:bg-slate-50"
                      }`}
                    >
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive ? "text-rr-pink" : "text-slate-400"
                        }`}
                      />
                      <span className="truncate">{item.name}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
