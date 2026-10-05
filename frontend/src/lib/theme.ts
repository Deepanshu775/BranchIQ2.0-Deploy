// BranchIQ design tokens — ported from the shipped BranchIQ UI so the 2.0 upgrade keeps
// the exact executive look (navy sidebar, light canvas, blue/cyan accents).

export const CHART = {
  primary: "#1687F8",
  dark: "#071426",
  accent: "#27C3E8",
  soft: "#60A5FA",
  light: "#DBEAFE",
  neutral: "#E2E8F0",
  muted: "#94A3B8",
  positive: "#16A36A",
  warning: "#E79B24",
  danger: "#D9534F",
  purple: "#7657D9",
  grid: "#EEF2F7",
  ink: "#0F172A",
  charcoal: "#0B1220",
};

export const CHART_SERIES = ["#1687F8", "#27C3E8", "#7657D9", "#16A36A", "#E79B24", "#071426"];

export function opportunityFill(score: number): string {
  if (score >= 80) return "#1D4ED8";
  if (score >= 72) return "#2563EB";
  if (score >= 64) return "#0891B2";
  if (score >= 56) return "#67E8F9";
  return "#DBEAFE";
}

export function opportunityText(score: number): string {
  return score >= 64 ? "#ffffff" : "#1E3A8A";
}

// Map marker colours (design_guidelines: green/yellow/red/grey by opportunity)
export function markerColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return "#94A3B8";
  if (score >= 80) return "#16A36A";
  if (score >= 65) return "#E79B24";
  return "#D9534F";
}

export const MARKER = {
  ownBranch: "#1687F8",
  competitor: "#64748B",
  insufficient: "#94A3B8",
};

export const DATA_LABEL_BADGES: Record<string, { label: string; cls: string }> = {
  official: { label: "OFFICIAL REPORTED DATA", cls: "bg-slate-100 text-slate-700 border-slate-300" },
  analytical: { label: "BRANCHIQ ANALYTICAL SCORE", cls: "bg-blue-50 text-blue-700 border-blue-200" },
  market: { label: "PUBLIC MARKET INDICATOR", cls: "bg-cyan-50 text-cyan-800 border-cyan-200" },
  model: { label: "MODEL-GENERATED ESTIMATE", cls: "bg-purple-50 text-purple-700 border-purple-200" },
  demo: { label: "DEMO DATA — DEVELOPMENT", cls: "bg-amber-50 text-amber-800 border-amber-300" },
  derived: { label: "BRANCHIQ DERIVED METRIC", cls: "bg-indigo-50 text-indigo-700 border-indigo-200" },
  prediction: { label: "ML MODEL PREDICTION", cls: "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200" },
};

export const CONFIDENCE: Record<string, { cls: string; dot: string }> = {
  HIGH: { cls: "bg-emerald-50 text-emerald-700 border-emerald-300", dot: "#16A36A" },
  MEDIUM: { cls: "bg-amber-50 text-amber-700 border-amber-300", dot: "#E79B24" },
  LIMITED: { cls: "bg-rose-50 text-rose-700 border-rose-300", dot: "#D9534F" },
  LOW: { cls: "bg-rose-50 text-rose-700 border-rose-300", dot: "#D9534F" },
  INSUFFICIENT: { cls: "bg-slate-100 text-slate-600 border-slate-300", dot: "#94A3B8" },
};

export const METHODOLOGY_NOTE =
  "BranchIQ combines publicly available banking, geographic and market indicators with its own " +
  "transparent analytical framework. Strategic scores are model-generated estimates, not official " +
  "bank forecasts; demo records are labelled as such.";

export const PRODUCT_PRINCIPLE =
  "Based on public banking data, market indicators, bank network presence, competitor density, " +
  "geospatial whitespace and BranchIQ's analytical model, this location appears to be a " +
  "high-priority opportunity for further branch feasibility evaluation.";

export function formatCrore(cr: number | null | undefined): string {
  if (cr === null || cr === undefined) return "Public figure unavailable";
  if (cr >= 100000) return `₹${(cr / 100000).toFixed(2)} L Cr`;
  return `₹${cr.toLocaleString("en-IN")} Cr`;
}

export function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined) return "Public figure unavailable";
  return n.toLocaleString("en-IN");
}

export function formatKm(km: number | null | undefined): string {
  if (km === null || km === undefined) return "—";
  return `${km.toFixed(1)} km`;
}

export const SCORE_WEIGHTS = [
  { key: "marketGrowth", label: "Market Growth", weight: 0.3, color: "#1687F8" },
  { key: "creditOpportunity", label: "Credit Opportunity", weight: 0.2, color: "#27C3E8" },
  { key: "depositOpportunity", label: "Deposit Opportunity", weight: 0.15, color: "#16A36A" },
  { key: "customerPotential", label: "Customer Potential", weight: 0.15, color: "#7657D9" },
  { key: "competitiveOpportunity", label: "Competitive Opportunity", weight: 0.1, color: "#E79B24" },
  { key: "digitalReadiness", label: "Digital Readiness", weight: 0.1, color: "#071426" },
];

export const TIER_LABELS: Record<string, string> = {
  tier1: "Tier-1 (Metro)",
  tier2: "Tier-2 (Urban)",
  tier3: "Tier-3+ (Semi-Urban / Rural)",
};
