import { Building2, Globe2, Landmark, Layers, Target } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  ChartCard,
  DataBadge,
  DecisionBadge,
  KpiCard,
  MethodologyNote,
  ScoreBar,
  ScoreRing,
  SectionTitle,
} from "@/components/shared/Ui";
import { useApp } from "@/context/AppContext";
import { useBanks, useStatesRanked } from "@/lib/branchiq";
import { CHART, SCORE_WEIGHTS, formatCrore, formatNumber } from "@/lib/theme";

export default function Dashboard() {
  const { selectedBank } = useApp();
  const { data: banks } = useBanks();
  const { data: ranked } = useStatesRanked(selectedBank);

  const list = banks ?? [];
  const rows = ranked ?? [];
  const index = rows.length ? Math.round(rows.reduce((a, r) => a + r.score, 0) / rows.length) : 0;
  const decision = rows.length ? rows[0].decision : { label: "—", color: "#64748B" };
  const components = SCORE_WEIGHTS.map((w) => ({
    ...w,
    value: rows.length ? Math.round(rows.reduce((a, r) => a + (r.sub[w.key] ?? 0), 0) / rows.length) : 0,
  }));
  const totalBranches = list.reduce((a, b) => a + b.branches, 0);
  const totalDeposits = list.reduce((a, b) => a + b.deposits, 0);
  const highOpps = rows.filter((r) => r.score >= 80).length;

  return (
    <div className="space-y-8" data-testid="page-dashboard">
      <section className="bq-fade">
        <div className="bq-hero bq-hero-grid rounded-[24px] p-6 text-white shadow-xl shadow-slate-900/10 lg:p-7">
          <div className="relative z-10">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-cyan-300">
              <span className="bq-live-dot h-2 w-2 rounded-full bg-cyan-300" /> BranchIQ 2.0 Intelligence Layer
            </div>
            <h1 className="font-display mt-3 max-w-3xl text-3xl font-extrabold leading-[1.06] tracking-tight sm:text-4xl lg:text-[44px]">
              From state strategy to <span className="text-cyan-300">exact branch locations.</span>
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-slate-300 lg:text-[15px]">
              District → town/city → PIN code → candidate site intelligence for {selectedBank}, with transparent
              opportunity scores, geospatial whitespace and cannibalization analysis.
            </p>
            <div className="mt-5 inline-flex items-center gap-3 rounded-xl border border-white/10 bg-white/[.07] px-4 py-3 backdrop-blur-xl">
              <span className="text-xs text-slate-300">India Opportunity Index</span>
              <span className="stat-num text-2xl text-cyan-300">{index}</span>
              <span className="text-xs text-slate-400">/100</span>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <KpiCard testid="kpi-card-banks" icon={Landmark} label="Banks Analysed" value={String(list.length).padStart(2, "0")} context="Public + Private sector" variant="dark" />
        <KpiCard testid="kpi-card-regions" icon={Globe2} label="States Evaluated" value={rows.length} context="With district drill-down" />
        <KpiCard testid="kpi-card-branches" icon={Building2} label="Branches Covered" value={formatNumber(totalBranches)} context="Aggregate reported network" badge={<DataBadge type="official" />} />
        <KpiCard testid="kpi-card-deposits" icon={Layers} label="Deposits Analysed" value={formatCrore(totalDeposits)} context="FY2025 reported" variant="tint" badge={<DataBadge type="official" />} />
        <KpiCard testid="kpi-card-opportunities" icon={Target} label="Priority Markets" value={highOpps} context="States scoring 80+" variant="accent" badge={<DataBadge type="analytical" />} />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <div className="bq-card bq-shadow flex flex-col items-center justify-center p-5 text-center" data-testid="opportunity-index-card">
          <div className="eyebrow">India Banking Opportunity Index</div>
          <div className="my-3">
            <ScoreRing value={index} size={180} stroke={16} color={decision.color} />
          </div>
          <div className="mb-2 text-sm text-slate-500">{selectedBank}</div>
          <DecisionBadge decision={decision} />
        </div>
        <div className="bq-card bq-shadow p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="accent-line text-sm font-bold text-[#0F172A]">Opportunity Score Components</h3>
            <DataBadge type="analytical" />
          </div>
          <div className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
            {components.map((w) => (
              <ScoreBar key={w.key} testid={`component-${w.key}`} label={`${w.label} · ${Math.round(w.weight * 100)}%`} value={w.value} color={w.color} />
            ))}
          </div>
          <MethodologyNote className="mt-5" />
        </div>
      </section>

      <section>
        <SectionTitle
          eyebrow="Priority Opportunities"
          title="Where should management look first?"
          subtitle={`Ranked state markets for ${selectedBank}. Drill into districts and exact locations in Location Intelligence.`}
          right={<DataBadge type="analytical" />}
          testid="section-priorities"
        />
        <ChartCard title="Opportunity score by state" eyebrow="Ranking" badge={<DataBadge type="analytical" />} testid="chart-state-ranking">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rows.map((r) => ({ name: r.state, value: r.score }))} margin={{ top: 18, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#64748b" }} interval={0} angle={-35} textAnchor="end" height={78} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#64748b" }} />
              <Tooltip formatter={(value: number) => [`${value}/100`, "Opportunity"]} cursor={{ fill: "#F8FAFC" }} />
              <Bar dataKey="value" name="Opportunity" radius={[4, 4, 0, 0]}>
                {rows.map((d, i) => (
                  <Cell key={i} fill={d.score >= 80 ? CHART.positive : d.score >= 70 ? CHART.primary : d.score >= 60 ? CHART.accent : CHART.soft} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {rows.slice(0, 6).map((p, idx) => (
            <div key={p.id} data-testid={`priority-card-${idx}`} className="bq-card bq-shadow bq-card-hover flex flex-col p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="stat-num flex h-7 w-7 items-center justify-center rounded-md bg-[#DBEAFE] text-xs font-bold text-[#1687F8]">
                    {idx + 1}
                  </span>
                  <div>
                    <div className="font-semibold text-[#0F172A]">{p.state}</div>
                    <div className="text-[10px] text-slate-400">{p.region} Region · {p.drivers[0]?.label}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="stat-num text-2xl text-[#0F172A]">{p.score}</div>
                  <div className="text-[10px] text-slate-400">Opportunity</div>
                </div>
              </div>
              <div className="mt-3 flex-1 rounded-md bg-[#F8FAFC] px-3 py-2 text-xs leading-relaxed text-slate-600">
                <span className="font-semibold text-slate-700">Recommended action: </span>
                {p.recommendation}
              </div>
              <div className="mt-3 flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Priority: <span className="text-[#0F172A]">{p.priority}</span>
                </span>
                <DecisionBadge decision={p.decision} />
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
