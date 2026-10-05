import { useState } from "react";
import { MapPin, Rocket, Search, Smartphone, TrendingUp, Wrench } from "lucide-react";

import {
  ConfidenceBadge,
  DataBadge,
  DecisionBadge,
  EmptyState,
  MethodologyNote,
  ScoreBar,
  SectionTitle,
} from "@/components/shared/Ui";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useApp } from "@/context/AppContext";
import { useStatesRanked } from "@/lib/branchiq";
import type { StateRanked } from "@/types/api";

const CATEGORIES = [
  { id: "expand", num: "01", title: "Expansion Opportunities", icon: Rocket, accent: "#16A36A", match: (o: StateRanked) => o.score >= 80 },
  { id: "selective", num: "02", title: "Selective Expansion", icon: TrendingUp, accent: "#1687F8", match: (o: StateRanked) => o.score >= 60 && o.score < 80 },
  { id: "optimize", num: "03", title: "Network Optimization", icon: Wrench, accent: "#E79B24", match: (o: StateRanked) => o.score >= 40 && o.score < 60 },
  { id: "digital", num: "04", title: "Digital-First Opportunities", icon: Smartphone, accent: "#7657D9", match: (o: StateRanked) => (o.sub.digitalReadiness ?? 0) >= 82 },
  { id: "review", num: "05", title: "Markets Requiring Further Review", icon: Search, accent: "#64748B", match: (o: StateRanked) => o.dataConfidence === "LIMITED" || o.score < 40 },
];

export default function Recommendations() {
  const { selectedBank } = useApp();
  const { data: ranked } = useStatesRanked(selectedBank);
  const [active, setActive] = useState<StateRanked | null>(null);
  const rows = ranked ?? [];

  return (
    <div className="space-y-8" data-testid="page-recommendations">
      <SectionTitle
        eyebrow="Executive Recommendation Board"
        title="Strategic Recommendations"
        subtitle={`Prioritised strategic actions for ${selectedBank}, generated from BranchIQ opportunity scores.`}
        testid="section-recommendations"
      />

      {rows.length === 0 ? (
        <EmptyState title="No recommendations yet" hint="Opportunity scores are loading." testid="recommendations-empty" />
      ) : (
        <div className="space-y-6">
          {CATEGORIES.map((cat) => {
            const items = rows.filter(cat.match);
            return (
              <section key={cat.id} data-testid={`rec-category-${cat.id}`}>
                <div className="mb-3 flex items-center gap-2">
                  <span className="font-mono text-xs text-slate-400">{cat.num}</span>
                  <span className="flex h-7 w-7 items-center justify-center rounded-md" style={{ background: `${cat.accent}18`, color: cat.accent }}>
                    <cat.icon size={15} />
                  </span>
                  <h3 className="font-display text-base font-bold text-[#071426]">{cat.title}</h3>
                  <span className="text-xs text-slate-400">({items.length})</span>
                </div>
                {items.length === 0 ? (
                  <div className="bq-card px-4 py-3 text-xs text-slate-400">
                    No markets currently classified under this category for {selectedBank}.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {items.map((o) => (
                      <button
                        key={o.id}
                        onClick={() => setActive(o)}
                        data-testid={`rec-card-${o.id}`}
                        className="bq-card bq-shadow bq-card-hover p-4 text-left"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-1.5 font-semibold text-[#071426]">
                            <MapPin size={14} className="text-[#1687F8]" />
                            {o.state}
                          </div>
                          <div className="text-right">
                            <div className="font-display text-xl font-bold text-[#071426]">{o.score}</div>
                            <div className="text-[10px] text-slate-400">Opportunity</div>
                          </div>
                        </div>
                        <div className="mt-0.5 text-[10px] text-slate-400">{selectedBank} · {o.region} Region</div>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {o.drivers.slice(0, 2).map((d) => (
                            <span key={d.key} className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-600">
                              {d.label}
                            </span>
                          ))}
                        </div>
                        <p className="mt-2 line-clamp-2 text-xs text-slate-600">{o.recommendation}</p>
                        <div className="mt-3 flex items-center justify-between">
                          <ConfidenceBadge level={o.dataConfidence} />
                          <DecisionBadge decision={o.decision} />
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}

      <MethodologyNote />

      <Dialog open={!!active} onOpenChange={(o: boolean) => !o && setActive(null)}>
        <DialogContent className="max-w-lg" data-testid="market-detail-dialog">
          {active && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-2">
                  <DataBadge type="analytical" />
                  <DecisionBadge decision={active.decision} />
                </div>
                <DialogTitle className="font-display mt-2 flex items-center gap-2 text-xl">
                  <MapPin size={18} className="text-[#1687F8]" />
                  {active.state}
                </DialogTitle>
              </DialogHeader>
              <div className="mb-2 flex items-center gap-4">
                <div>
                  <div className="font-display text-3xl font-bold text-[#071426]">{active.score}</div>
                  <div className="text-[10px] text-slate-400">Opportunity / 100</div>
                </div>
                <div className="text-sm text-slate-600">
                  {selectedBank} · {active.region} Region
                  <br />
                  <span className="text-xs text-slate-400">Priority: {active.priority}</span>
                </div>
              </div>
              <div className="space-y-2.5">
                {Object.entries(active.sub).map(([k, v]) => (
                  <ScoreBar key={k} label={k.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase())} value={v} />
                ))}
              </div>
              <div className="mt-3 rounded-lg bg-[#F4F7FB] p-3">
                <div className="eyebrow mb-1">Recommended Action</div>
                <p className="text-sm text-slate-700">{active.recommendation}</p>
              </div>
              <div className="mt-2">
                <ConfidenceBadge level={active.dataConfidence} />
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
