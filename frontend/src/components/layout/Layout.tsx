import { Building2, FileDown, Menu } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  BookOpen,
  Bot,
  Compass,
  LayoutGrid,
  Map as MapIcon,
  MapPin,
  Network as NetworkIcon,
  ShieldCheck,
  Sparkles,
  UserCircle2,
  X,
} from "lucide-react";

import ExecutiveReport from "@/components/ExecutiveReport";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useApp } from "@/context/AppContext";
import { useBanks } from "@/lib/branchiq";

const NAV = [
  { name: "Overview", to: "/", icon: LayoutGrid, end: true },
  { name: "Location Intelligence", to: "/location-intelligence", icon: MapPin, badge: "2.0" },
  { name: "Bank Intelligence", to: "/comparison", icon: Building2 },
  { name: "Network Analysis", to: "/network", icon: NetworkIcon },
  { name: "Opportunity Map", to: "/opportunity-map", icon: MapIcon },
  { name: "AI Consultant", to: "/consultant", icon: Bot },
  { name: "Strategic Recommendations", to: "/recommendations", icon: Compass },
  { name: "Model & Training", to: "/model", icon: Sparkles },
  { name: "Sources & Methodology", to: "/methodology", icon: BookOpen },
];

const TITLES: Record<string, [string, string]> = {
  "/": ["Executive Dashboard", "Indian Banking Network Intelligence"],
  "/location-intelligence": ["Location Intelligence", "Which exact districts, towns and locations — and why?"],
  "/comparison": ["Bank Intelligence", "How does each bank compare?"],
  "/network": ["Network Intelligence", "Where is the network strong — and where is the whitespace?"],
  "/opportunity-map": ["Opportunity Map", "Where should banks expand next?"],
  "/consultant": ["BranchIQ Consultant", "What should management do?"],
  "/recommendations": ["Strategic Recommendations", "What actions should be prioritized?"],
  "/model": ["Model & Training", "What does the trained model predict — and why?"],
  "/methodology": ["Sources & Methodology", "Can you trust the analysis?"],
};

export function BankSelector({ testid = "bank-selector-dropdown", className = "" }: { testid?: string; className?: string }) {
  const { selectedBank, setSelectedBank } = useApp();
  const { data: banks } = useBanks();
  const list = banks ?? [];
  const groups = [
    { group: "Public Sector Banks", items: list.filter((b) => b.sector === "Public") },
    { group: "Private Sector Banks", items: list.filter((b) => b.sector === "Private") },
  ];
  return (
    <Select value={selectedBank} onValueChange={(v: string) => setSelectedBank(v)}>
      <SelectTrigger
        data-testid={testid}
        className={`h-9 w-[210px] shrink-0 border-[#E2E8F0] bg-white text-sm font-semibold text-[#0F172A] ${className}`}
      >
        <span className="flex items-center gap-2 truncate">
          <Building2 size={15} className="shrink-0 text-[#1687F8]" />
          {/* base-ui renders the RAW value, so map value → label explicitly */}
          <SelectValue placeholder="Select a bank">{(v) => String(v ?? selectedBank)}</SelectValue>
        </span>
      </SelectTrigger>
      <SelectContent className="max-h-[380px]">
        {groups.map((g) =>
          g.items.length ? (
            <SelectGroup key={g.group}>
              <SelectLabel className="text-[10px] uppercase tracking-wider text-slate-400">{g.group}</SelectLabel>
              {g.items.map((b) => (
                <SelectItem
                  key={b.short}
                  value={b.short}
                  data-testid={`bank-option-${b.short.replace(/[^a-zA-Z]+/g, "-").toLowerCase()}`}
                >
                  {b.short}
                </SelectItem>
              ))}
            </SelectGroup>
          ) : null,
        )}
      </SelectContent>
    </Select>
  );
}

function Sidebar() {
  const { navOpen, setNavOpen } = useApp();
  return (
    <aside
      data-testid="app-sidebar"
      style={{ transform: navOpen ? "translateX(0)" : "translateX(-100%)" }}
      className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/5 bg-[#0B1220] text-white transition-transform duration-300"
    >
      <div className="border-b border-white/[.07] px-5 py-5">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 shadow-lg shadow-blue-950/40">
            <Sparkles size={20} color="#fff" strokeWidth={2.2} />
          </span>
          <div className="leading-tight">
            <div className="font-display text-lg font-extrabold tracking-tight">
              BRANCH<span className="text-cyan-400">IQ</span>
              <span className="ml-1 text-[10px] font-bold text-cyan-300">2.0</span>
            </div>
            <div className="mt-0.5 text-[10px] text-slate-400">Branch Expansion Intelligence</div>
          </div>
          <button
            onClick={() => setNavOpen(false)}
            aria-label="Close navigation"
            data-testid="nav-close-btn"
            className="ml-auto flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-white/[.08] hover:text-white"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      <nav className="bq-scroll flex-1 space-y-1 overflow-y-auto px-3 py-5">
        <div className="eyebrow px-3 pb-2 text-slate-500">Workspace</div>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setNavOpen(false)}
            data-testid={`nav-${item.name.toLowerCase().replace(/[^a-z]+/g, "-").replace(/(^-|-$)/g, "")}`}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all ${
                isActive
                  ? "bg-blue-600/15 font-semibold text-white shadow-inner"
                  : "text-slate-400 hover:bg-white/[.045] hover:text-white"
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute bottom-2 left-0 top-2 w-1 rounded-full bg-gradient-to-b from-blue-400 to-cyan-400" />
                )}
                <item.icon
                  size={18}
                  className={`shrink-0 ${isActive ? "text-cyan-300" : "text-slate-500 group-hover:text-slate-200"}`}
                />
                <span className="leading-tight">{item.name}</span>
                {item.badge && (
                  <span className="ml-auto rounded bg-cyan-400/20 px-1.5 py-0.5 text-[9px] font-bold text-cyan-300">
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/[.07] px-4 py-4">
        <div className="eyebrow mb-2 text-slate-500">Data Coverage</div>
        <div className="mb-3 grid grid-cols-3 gap-2">
          {[
            ["9", "Banks"],
            ["24", "States"],
            ["170+", "Districts"],
          ].map(([n, l]) => (
            <div key={l} className="rounded-xl border border-white/[.05] bg-white/[.045] px-2 py-2 text-center">
              <div className="stat-num text-sm text-white">{n}</div>
              <div className="text-[9px] uppercase tracking-wide text-slate-500">{l}</div>
            </div>
          ))}
        </div>
        <div className="mb-3 flex items-start gap-2 rounded-xl border border-amber-400/20 bg-amber-400/10 px-2.5 py-2">
          <ShieldCheck size={14} className="mt-0.5 shrink-0 text-amber-300" />
          <p className="text-[9px] leading-snug text-amber-200">
            Branch placement &amp; locality economics are DEMO data. Bank financials are official FY2025 figures.
          </p>
        </div>
        <div className="flex items-center gap-2.5 rounded-xl border border-white/[.05] bg-white/[.045] px-3 py-2.5">
          <UserCircle2 size={30} className="text-cyan-300" />
          <div className="leading-tight">
            <div className="text-sm font-semibold text-white">BranchIQ Analyst</div>
            <div className="text-[10px] text-slate-500">Strategy Workspace</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function Header() {
  const { setReportOpen, toggleNav } = useApp();
  const { pathname } = useLocation();
  const [title, subtitle] = TITLES[pathname] ?? TITLES["/"];
  return (
    <header
      data-testid="app-header"
      className="sticky top-0 z-30 border-b border-[#E5EAF2] bg-white/85 backdrop-blur-xl"
    >
      <div className="flex items-center gap-3 px-4 py-3 lg:px-7">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleNav}
          data-testid="nav-toggle-btn"
          className="shrink-0 text-slate-500 hover:bg-blue-50 hover:text-blue-600"
        >
          <Menu size={20} />
        </Button>

        <div className="min-w-0 flex-1 px-1 lg:px-3">
          <h1 className="font-display truncate text-base font-extrabold leading-none tracking-tight text-[#0F172A] lg:text-lg">
            {title}
          </h1>
          <div className="mt-1 hidden truncate text-[10px] text-slate-400 sm:block">{subtitle}</div>
        </div>

        <div className="mr-1 hidden items-center gap-4 xl:flex">
          <div className="flex flex-col leading-tight">
            <span className="eyebrow">Data Period</span>
            <span className="text-xs font-semibold text-slate-700">FY2024–25</span>
          </div>
          <div className="h-7 w-px bg-slate-200" />
          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600">
            <span className="bq-live-dot h-2 w-2 rounded-full bg-emerald-500" />
            Public Data Connected
          </div>
        </div>

        <BankSelector />
        <Button
          data-testid="btn-generate-report"
          onClick={() => setReportOpen(true)}
          className="h-9 gap-2 rounded-xl bg-[#1687F8] text-sm font-semibold text-white shadow-sm shadow-blue-600/20 hover:bg-[#0F6FD4]"
        >
          <FileDown size={15} />
          <span className="hidden sm:inline">Generate Report</span>
        </Button>
      </div>
    </header>
  );
}

export default function Layout() {
  const { navOpen, setNavOpen } = useApp();
  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      {navOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40"
          onClick={() => setNavOpen(false)}
          data-testid="nav-backdrop"
        />
      )}
      <div className="bq-grid-bg flex min-h-screen flex-col">
        <Header />
        <main className="mx-auto w-full max-w-[1600px] flex-1 px-4 py-6 lg:px-6">
          <Outlet />
        </main>
      </div>
      <ExecutiveReport />
    </div>
  );
}
