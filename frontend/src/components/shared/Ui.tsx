import { Info, TrendingDown, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";

import { CONFIDENCE, DATA_LABEL_BADGES, METHODOLOGY_NOTE } from "@/lib/theme";
import type { Decision } from "@/types/api";

export function DataBadge({ type, className = "" }: { type: string; className?: string }) {
  const b = DATA_LABEL_BADGES[type] ?? DATA_LABEL_BADGES.model;
  return (
    <span
      data-testid={`data-badge-${type}`}
      className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${b.cls} ${className}`}
    >
      {b.label}
    </span>
  );
}

export function ConfidenceBadge({ level = "MEDIUM", className = "" }: { level?: string; className?: string }) {
  const c = CONFIDENCE[level] ?? CONFIDENCE.MEDIUM;
  return (
    <span
      data-testid={`confidence-badge-${level.toLowerCase()}`}
      className={`inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-[10px] font-semibold ${c.cls} ${className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: c.dot }} />
      DATA CONFIDENCE: {level}
    </span>
  );
}

export function DecisionBadge({ decision, className = "" }: { decision: Decision; className?: string }) {
  return (
    <span
      data-testid="decision-badge"
      className={`inline-flex items-center rounded border px-2.5 py-1 text-xs font-bold tracking-wide ${className}`}
      style={{ background: `${decision.color}15`, color: decision.color, borderColor: `${decision.color}55` }}
    >
      {decision.label}
    </span>
  );
}

export function RiskBadge({ risk }: { risk: string }) {
  const map: Record<string, string> = {
    HIGH: "bg-rose-50 text-rose-700 border-rose-300",
    MEDIUM: "bg-amber-50 text-amber-700 border-amber-300",
    LOW: "bg-emerald-50 text-emerald-700 border-emerald-300",
    NONE: "bg-slate-50 text-slate-600 border-slate-300",
  };
  return (
    <span
      data-testid={`risk-badge-${risk.toLowerCase()}`}
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-bold ${map[risk] ?? map.NONE}`}
    >
      CANNIBALIZATION: {risk}
    </span>
  );
}

export function SectionTitle({
  eyebrow,
  title,
  subtitle,
  right,
  testid,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  right?: ReactNode;
  testid?: string;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3" data-testid={testid}>
      <div className="accent-line">
        {eyebrow && <div className="eyebrow mb-1">{eyebrow}</div>}
        <h2 className="font-display text-xl font-bold tracking-tight text-[#0F172A] lg:text-2xl">{title}</h2>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-slate-500">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

export function MethodologyNote({ className = "", text }: { className?: string; text?: string }) {
  return (
    <div
      className={`flex items-start gap-2 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2.5 ${className}`}
      data-testid="methodology-note"
    >
      <Info size={15} className="mt-0.5 shrink-0 text-blue-600" />
      <p className="text-xs leading-relaxed text-slate-600">{text ?? METHODOLOGY_NOTE}</p>
    </div>
  );
}

export function ChartCard({
  title,
  eyebrow,
  badge,
  children,
  className = "",
  testid,
}: {
  title: string;
  eyebrow?: string;
  badge?: ReactNode;
  children: ReactNode;
  className?: string;
  testid?: string;
}) {
  return (
    <div className={`bq-card bq-shadow p-4 ${className}`} data-testid={testid}>
      <div className="mb-3 flex items-start justify-between">
        <div>
          {eyebrow && <div className="eyebrow mb-0.5">{eyebrow}</div>}
          <h3 className="text-sm font-bold text-[#0F172A]">{title}</h3>
        </div>
        {badge}
      </div>
      {children}
    </div>
  );
}

export function ScoreRing({
  value = 0,
  size = 140,
  stroke = 12,
  color = "#1687F8",
  label,
  sublabel,
  testid,
}: {
  value?: number;
  size?: number;
  stroke?: number;
  color?: string;
  label?: string;
  sublabel?: string;
  testid?: string;
}) {
  const radius = (size - stroke) / 2;
  const circ = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, value));
  const offset = circ - (pct / 100) * circ;
  return (
    <div className="flex flex-col items-center" data-testid={testid}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#F1F5F9" strokeWidth={stroke} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.22,1,0.36,1)" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="stat-num leading-none" style={{ fontSize: size * 0.28, color: "#0F172A" }}>
            {Math.round(value)}
          </span>
          <span className="mt-0.5 text-[10px] font-semibold text-slate-400">/ 100</span>
        </div>
      </div>
      {label && <div className="mt-2 text-center text-sm font-semibold text-[#111827]">{label}</div>}
      {sublabel && <div className="text-center text-xs text-slate-500">{sublabel}</div>}
    </div>
  );
}

export function ScoreBar({
  label,
  value,
  color = "#1687F8",
  suffix = "/100",
  testid,
}: {
  label: string;
  value: number;
  color?: string;
  suffix?: string;
  testid?: string;
}) {
  return (
    <div data-testid={testid}>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600">{label}</span>
        <span className="stat-num text-xs font-bold text-[#0F172A]">
          {value}
          {suffix}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full"
          style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: color, transition: "width 0.8s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </div>
    </div>
  );
}

const KPI_VARIANTS: Record<string, { card: string; label: string; value: string; sub: string }> = {
  default: { card: "bg-white border-[#E5EAF2]", label: "text-slate-500", value: "text-[#0F172A]", sub: "text-slate-400" },
  // Explicit light tints on the dark card: the global light-theme readability floor darkens
  // text-slate-400/500, which would be unreadable on #0B1220.
  dark: { card: "bg-[#0B1220] border-[#0B1220]", label: "text-[#CBD5E1]", value: "text-white", sub: "text-[#94A3B8]" },
  accent: { card: "bg-gradient-to-br from-blue-600 to-blue-700 border-blue-600", label: "text-blue-100", value: "text-white", sub: "text-blue-100/80" },
  tint: { card: "bg-blue-50/70 border-blue-100", label: "text-blue-600", value: "text-[#0F172A]", sub: "text-slate-500" },
};

export function KpiCard({
  testid,
  icon: Icon,
  accent = "#1687F8",
  label,
  value,
  unit,
  context,
  delta,
  badge,
  variant = "default",
}: {
  testid?: string;
  icon?: React.ComponentType<{ size?: number }>;
  accent?: string;
  label: string;
  value: ReactNode;
  unit?: string;
  context?: string;
  delta?: number | null;
  badge?: ReactNode;
  variant?: string;
}) {
  const v = KPI_VARIANTS[variant] ?? KPI_VARIANTS.default;
  const dark = variant === "dark" || variant === "accent";
  const iconTint = dark
    ? { background: "rgba(255,255,255,.12)", color: "#fff" }
    : { background: `${accent}12`, color: accent };
  return (
    <div
      data-testid={testid}
      className={`bq-shadow bq-card-hover relative flex min-h-[150px] flex-col overflow-hidden rounded-[18px] border p-4 ${v.card}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          {Icon && (
            <span className="flex h-9 w-9 items-center justify-center rounded-xl" style={iconTint}>
              <Icon size={17} />
            </span>
          )}
          <span className={`text-[10px] font-bold uppercase tracking-[0.08em] ${v.label}`}>{label}</span>
        </div>
        {delta !== undefined && delta !== null && (
          <span
            className={`inline-flex items-center gap-0.5 text-xs font-semibold ${
              dark ? "text-white/90" : delta >= 0 ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {delta >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />} {Math.abs(delta)}%
          </span>
        )}
      </div>
      <div className="mt-4 flex items-baseline gap-1">
        <span className={`stat-num text-3xl ${v.value}`}>{value}</span>
        {unit && <span className={`text-sm font-medium ${v.sub}`}>{unit}</span>}
      </div>
      {context && <div className={`mt-1 text-xs ${v.sub}`}>{context}</div>}
      <div className="mt-auto flex items-center justify-end gap-2 pt-3">{badge}</div>
    </div>
  );
}

export function EmptyState({ title, hint, testid }: { title: string; hint?: string; testid?: string }) {
  return (
    <div className="bq-card px-4 py-8 text-center" data-testid={testid}>
      <div className="text-sm font-semibold text-slate-600">{title}</div>
      {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
    </div>
  );
}
