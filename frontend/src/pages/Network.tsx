import { useState } from "react";
import { AlertTriangle, HandCoins, MapPin, PiggyBank, Smartphone, Swords, TrendingUp, Users } from "lucide-react";

import {
  ConfidenceBadge,
  DataBadge,
  DecisionBadge,
  EmptyState,
  MethodologyNote,
  ScoreBar,
  ScoreRing,
  SectionTitle,
} from "@/components/shared/Ui";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useApp } from "@/context/AppContext";
import { useDistrictsRanked, useMarketOverview, useStates, useStatesRanked } from "@/lib/branchiq";
import { SCORE_WEIGHTS, TIER_LABELS, formatNumber } from "@/lib/theme";

function IntelPanel({
  icon: Icon,
  label,
  value,
  sub,
  badge,
  accent = "#1687F8",
  testid,
}: {
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  value: string;
  sub?: string;
  badge?: React.ReactNode;
  accent?: string;
  testid?: string;
}) {
  return (
    <div className="bq-card bq-shadow p-4" data-testid={testid}>
      <div className="mb-2 flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-md" style={{ background: `${accent}14`, color: accent }}>
          <Icon size={16} />
        </span>
        <span className="eyebrow">{label}</span>
      </div>
      <div className="font-display text-xl font-bold text-[#071426]">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
      {badge && <div className="mt-2">{badge}</div>}
    </div>
  );
}

export default function Network() {
  const { selectedBank, stateId, districtId, selectState, selectDistrict } = useApp();
  const { data: states } = useStates();
  const { data: statesRanked } = useStatesRanked(selectedBank);
  const { data: districts } = useDistrictsRanked(stateId, selectedBank);
  const { data: market } = useMarketOverview(districtId);
  const [showFormula, setShowFormula] = useState(false);

  const stateList = states ?? [];
  const stateRow = (statesRanked ?? []).find((s) => s.id === stateId) ?? (statesRanked ?? [])[0];
  const districtRow = (districts ?? []).find((d) => d.id === districtId);
  const active = districtRow ?? null;
  const sub = active ? active.sub : stateRow?.sub;
  const overall = active ? active.overall : stateRow?.score;
  const decision = active ? active.decision : stateRow?.decision;
  const confidence = active ? active.dataConfidence : stateRow?.dataConfidence;

  const SUB_META: Record<string, { icon: React.ComponentType<{ size?: number }>; label: string; color: string }> = {
    marketGrowth: { icon: TrendingUp, label: "Market Growth Score", color: "#1687F8" },
    creditOpportunity: { icon: HandCoins, label: "Credit Opportunity Score", color: "#27C3E8" },
    depositOpportunity: { icon: PiggyBank, label: "Deposit Opportunity Score", color: "#16A36A" },
    customerPotential: { icon: Users, label: "Customer Potential Score", color: "#7657D9" },
    competitiveOpportunity: { icon: Swords, label: "Competitive Opportunity Score", color: "#E79B24" },
    digitalReadiness: { icon: Smartphone, label: "Digital Readiness Score", color: "#071426" },
  };

  return (
    <div className="space-y-8" data-testid="page-network">
      <SectionTitle
        eyebrow="Market Intelligence"
        title="Network Analysis"
        subtitle="Evaluate the bank's positioning and market whitespace at state or district level."
        testid="section-network"
      />

      <div className="bq-card bq-shadow flex flex-wrap items-end gap-4 p-4" data-testid="network-filters">
        <div>
          <div className="eyebrow mb-1">State</div>
          <Select
            value={stateId ?? ""}
            onValueChange={(v: string) => selectState(v, stateList.find((s) => s.id === v)?.name ?? null)}
          >
            <SelectTrigger data-testid="filter-state-select" className="h-9 w-[200px] border-[#DFE7F0] bg-white text-sm font-semibold">
              <span className="flex items-center gap-2">
                <MapPin size={15} className="text-[#1687F8]" />
                <SelectValue placeholder="All India">
                  {(v) => stateList.find((s) => s.id === String(v))?.name ?? "All India"}
                </SelectValue>
              </span>
            </SelectTrigger>
            <SelectContent className="max-h-[340px]">
              {stateList.map((s) => (
                <SelectItem key={s.id} value={s.id} data-testid={`network-state-option-${s.id}`}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <div className="eyebrow mb-1">District</div>
          <Select
            value={districtId ?? ""}
            onValueChange={(v: string) => selectDistrict(v, (districts ?? []).find((d) => d.id === v)?.name ?? null)}
          >
            <SelectTrigger
              data-testid="filter-district-select"
              className="h-9 w-[220px] border-[#DFE7F0] bg-white text-sm font-semibold"
              disabled={!stateId}
            >
              <SelectValue placeholder={stateId ? "All districts" : "Select a state first"}>
                {(v) => (districts ?? []).find((d) => d.id === String(v))?.name ?? "All districts"}
              </SelectValue>
            </SelectTrigger>
            <SelectContent className="max-h-[340px]">
              {(districts ?? []).map((d) => (
                <SelectItem key={d.id} value={d.id}>
                  {d.name} · {TIER_LABELS[d.tier] ?? d.tier}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="ml-auto self-center">{confidence && <ConfidenceBadge level={confidence} />}</div>
      </div>

      {confidence === "LIMITED" && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2.5" data-testid="low-confidence-warning">
          <AlertTriangle size={15} className="mt-0.5 shrink-0 text-rose-500" />
          <p className="text-xs text-rose-700">
            Insufficient public evidence for a high-confidence recommendation in this market. Analytical estimate —
            management validation required.
          </p>
        </div>
      )}

      {!sub || !overall || !decision ? (
        <EmptyState title="Select a market" hint="Choose a state to compute network intelligence." testid="network-empty" />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
            <IntelPanel testid="intel-market" icon={TrendingUp} accent="#1687F8" label="Market Opportunity" value={`${overall}/100`} sub="Overall opportunity score" badge={<DataBadge type="analytical" />} />
            <IntelPanel testid="intel-deposit" icon={PiggyBank} accent="#16A36A" label="Deposit Environment" value={`${sub.depositOpportunity}/100`} sub="Deposit growth indicator" badge={<DataBadge type="model" />} />
            <IntelPanel testid="intel-credit" icon={HandCoins} accent="#E79B24" label="Credit Environment" value={`${sub.creditOpportunity}/100`} sub="Credit growth indicator" badge={<DataBadge type="model" />} />
            <IntelPanel testid="intel-digital" icon={Smartphone} accent="#071426" label="Digital Readiness" value={`${sub.digitalReadiness}/100`} sub="Digital adoption indicator" badge={<DataBadge type="market" />} />
            {active && (
              <>
                <IntelPanel testid="intel-own-branches" icon={MapPin} accent="#1687F8" label={`${selectedBank} branches`} value={String(active.ownBranches)} sub={`${active.penetrationPct}% of district network`} badge={<DataBadge type="demo" />} />
                <IntelPanel testid="intel-competitors" icon={Swords} accent="#D9534F" label="Competitor branches" value={String(active.competitorBranches)} sub={`${active.totalBranches} branches total`} badge={<DataBadge type="demo" />} />
                <IntelPanel testid="intel-population" icon={Users} accent="#7657D9" label="District population" value={`${active.populationMn} Mn`} sub={TIER_LABELS[active.tier] ?? active.tier} badge={<DataBadge type="market" />} />
                {market?.metrics?.cdRatio !== undefined && (
                  <IntelPanel testid="intel-cd-ratio" icon={HandCoins} accent="#27C3E8" label="Credit-Deposit ratio" value={`${market.metrics.cdRatio}%`} sub={`Deposits ₹${formatNumber(Number(market.metrics.depositVolumeCr))} Cr`} badge={<DataBadge type="model" />} />
                )}
              </>
            )}
          </div>

          <section className="bq-card bq-shadow p-5 lg:p-6">
            <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="eyebrow">Branch Opportunity Score</div>
                <h3 className="font-display text-lg font-bold text-[#071426]">
                  {selectedBank} · {active ? active.name : stateRow?.state}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <DataBadge type="analytical" />
                <DecisionBadge decision={decision} />
              </div>
            </div>
            <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-[220px_1fr]">
              <div className="flex justify-center">
                <ScoreRing value={overall} size={180} stroke={16} color={decision.color} label="Overall Opportunity" testid="score-ring-overall" />
              </div>
              <div className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
                {Object.keys(SUB_META).map((k) => (
                  <ScoreBar key={k} testid={`subscore-${k}`} label={SUB_META[k].label} value={sub[k] ?? 0} color={SUB_META[k].color} />
                ))}
              </div>
            </div>

            <button
              data-testid="formula-toggle"
              onClick={() => setShowFormula((v) => !v)}
              className="mt-5 w-full rounded-lg border border-[#DFE7F0] px-4 py-3 text-left text-sm font-semibold text-[#071426] hover:bg-[#F8FAFC]"
            >
              How is this score calculated? {showFormula ? "−" : "+"}
            </button>
            {showFormula && (
              <div className="mt-3 rounded-lg border border-[#DFE7F0] p-4" data-testid="formula-panel">
                <p className="mb-3 text-xs text-slate-500">
                  Opportunity Score = weighted sum of six analytical components, rounded to the nearest integer. Weights
                  are configurable server-side.
                </p>
                <div className="space-y-2">
                  {SCORE_WEIGHTS.map((w) => (
                    <div key={w.key} className="flex items-center gap-3">
                      <span className="w-40 text-xs text-slate-600">{w.label}</span>
                      <span className="w-14 font-mono text-xs text-slate-400">×{w.weight}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                        <div className="h-full rounded-full" style={{ width: `${w.weight * 100}%`, background: w.color }} />
                      </div>
                      <span className="w-12 text-right font-mono text-xs font-semibold text-[#0C1D33]">{sub[w.key] ?? 0}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-3 rounded bg-[#F4F7FB] p-3 font-mono text-xs leading-relaxed text-slate-600">
                  {SCORE_WEIGHTS.map((w) => `${sub[w.key] ?? 0}×${w.weight}`).join(" + ")} ={" "}
                  <span className="font-bold text-[#071426]">{overall}</span>
                </div>
              </div>
            )}
          </section>
        </>
      )}

      <MethodologyNote />
    </div>
  );
}
