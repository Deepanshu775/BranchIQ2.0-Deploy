import { FileDown, Network, Printer, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useApp } from "@/context/AppContext";
import { useBanks, useDistrictsRanked, useRankedLocations, useStatesRanked } from "@/lib/branchiq";
import { PRODUCT_PRINCIPLE, formatCrore, formatKm, formatNumber } from "@/lib/theme";

function Section({ n, title, children }: { n: string; title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <h2 className="font-display mb-2 flex items-center gap-2 text-base font-bold text-[#071426]">
        <span className="flex h-6 w-6 items-center justify-center rounded bg-[#071426] font-mono text-xs text-white">{n}</span>
        {title}
      </h2>
      {children}
    </div>
  );
}

export default function ExecutiveReport() {
  const { reportOpen, setReportOpen, selectedBank, stateId, stateName, districtId, districtName, cityId } = useApp();
  const { data: banks } = useBanks();
  const { data: states } = useStatesRanked(selectedBank);
  const { data: districts } = useDistrictsRanked(stateId, selectedBank);
  const { data: locations } = useRankedLocations({ stateId, districtId, cityId }, selectedBank, { limit: 10 });

  const bank = (banks ?? []).find((b) => b.short === selectedBank);
  const rows = states ?? [];
  const top5 = rows.slice(0, 5);
  const index = rows.length ? Math.round(rows.reduce((a, r) => a + r.score, 0) / rows.length) : 0;
  const today = new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
  const scope = districtName ?? stateName ?? "All India";

  return (
    <Dialog open={reportOpen} onOpenChange={setReportOpen}>
      <DialogContent className="bq-scroll max-h-[92vh] max-w-4xl overflow-y-auto p-0" data-testid="executive-report-dialog">
        <DialogTitle className="sr-only">BranchIQ Executive Report — {selectedBank}</DialogTitle>
        <div className="no-print sticky top-0 z-10 flex items-center justify-between bg-[#071426] px-5 py-3 text-white">
          <span className="font-display font-bold">Executive Report Preview · {scope}</span>
          <div className="flex items-center gap-2">
            <Button data-testid="btn-print-report" onClick={() => window.print()} size="sm" className="gap-1.5 bg-[#1687F8] hover:bg-[#0F6FD4]">
              <Printer size={14} />
              Print
            </Button>
            <Button data-testid="btn-download-pdf" onClick={() => window.print()} size="sm" variant="secondary" className="gap-1.5">
              <FileDown size={14} />
              PDF
            </Button>
            <button onClick={() => setReportOpen(false)} className="rounded p-1 hover:bg-white/10" aria-label="Close report">
              <X size={18} />
            </button>
          </div>
        </div>

        <div id="executive-report" className="bg-white p-8 text-[#0C1D33]">
          <div className="mb-6 border-b-2 border-[#071426] pb-5">
            <div className="mb-3 flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ background: "linear-gradient(135deg,#1687F8,#27C3E8)" }}>
                <Network size={22} color="#fff" />
              </span>
              <div>
                <div className="font-display text-2xl font-extrabold tracking-tight">BRANCHIQ 2.0</div>
                <div className="text-xs text-slate-500">Branch Expansion Intelligence Platform</div>
              </div>
            </div>
            <h1 className="font-display mt-4 text-xl font-bold">Branch Expansion Assessment — {selectedBank}</h1>
            <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
              <span><b>Bank:</b> {bank?.name ?? selectedBank}</span>
              <span><b>Sector:</b> {bank?.sector ?? "—"}</span>
              <span><b>Scope:</b> {scope}</span>
              <span><b>Period:</b> {bank?.reportingPeriod ?? "FY2025"}</span>
              <span><b>Generated:</b> {today}</span>
            </div>
          </div>

          <Section n="1" title="Executive Summary">
            <p className="text-sm leading-relaxed">
              {bank?.name ?? selectedBank} operates {formatNumber(bank?.branches)} branches with deposits of{" "}
              {formatCrore(bank?.deposits)} and advances of {formatCrore(bank?.advances)} ({bank?.reportingPeriod},
              source: {bank?.source}). BranchIQ assigns a national opportunity index of <b>{index}/100</b>
              {top5[0] && <> with <b>{top5[0].state}</b> the strongest market at {top5[0].score}/100 ({top5[0].decision.label})</>}.
              {districtName && <> Within {stateName}, the {districtName} district analysis and candidate-location ranking follow below.</>}
            </p>
          </Section>

          <Section n="2" title="Network Overview (Official Reported Data)">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["Branch Network", formatNumber(bank?.branches)],
                ["Deposits", formatCrore(bank?.deposits)],
                ["Advances", formatCrore(bank?.advances)],
                ["Coverage Index", `${bank?.geographicCoverage ?? "—"}/100`],
              ].map(([l, v]) => (
                <div key={l} className="rounded-lg border border-[#DFE7F0] p-3">
                  <div className="text-[10px] uppercase tracking-wide text-slate-400">{l}</div>
                  <div className="font-display text-lg font-bold">{v}</div>
                </div>
              ))}
            </div>
          </Section>

          <Section n="3" title="Market Attractiveness — Top 5 States">
            <table className="w-full border border-[#DFE7F0] text-sm">
              <thead>
                <tr className="bg-[#F4F7FB] text-left text-[11px] uppercase text-slate-500">
                  <th className="px-3 py-2">Market</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Priority</th>
                  <th className="px-3 py-2">Stance</th>
                </tr>
              </thead>
              <tbody>
                {top5.map((o) => (
                  <tr key={o.id} className="border-t border-[#EEF2F8]">
                    <td className="px-3 py-2 font-medium">{o.state}</td>
                    <td className="px-3 py-2 font-mono">{o.score}/100</td>
                    <td className="px-3 py-2">{o.priority}</td>
                    <td className="px-3 py-2 font-semibold" style={{ color: o.decision.color }}>{o.decision.label}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>

          {stateId && districts && districts.length > 0 && (
            <Section n="4" title={`District Ranking — ${stateName}`}>
              <table className="w-full border border-[#DFE7F0] text-sm">
                <thead>
                  <tr className="bg-[#F4F7FB] text-left text-[11px] uppercase text-slate-500">
                    <th className="px-3 py-2">District</th>
                    <th className="px-3 py-2 text-right">Own</th>
                    <th className="px-3 py-2 text-right">Competitors</th>
                    <th className="px-3 py-2 text-right">Score</th>
                    <th className="px-3 py-2">Stance</th>
                  </tr>
                </thead>
                <tbody>
                  {districts.slice(0, 8).map((d) => (
                    <tr key={d.id} className="border-t border-[#EEF2F8]">
                      <td className="px-3 py-2 font-medium">{d.name}</td>
                      <td className="px-3 py-2 text-right font-mono">{d.ownBranches}</td>
                      <td className="px-3 py-2 text-right font-mono">{d.competitorBranches}</td>
                      <td className="px-3 py-2 text-right font-mono">{d.overall}/100</td>
                      <td className="px-3 py-2 text-xs font-semibold" style={{ color: d.decision.color }}>{d.decision.label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          <div className="report-page-break" />

          {locations && locations.length > 0 && (
            <Section n="5" title="Candidate Branch Locations (Ranked)">
              <table className="w-full border border-[#DFE7F0] text-xs">
                <thead>
                  <tr className="bg-[#F4F7FB] text-left text-[10px] uppercase text-slate-500">
                    <th className="px-2 py-2">#</th>
                    <th className="px-2 py-2">Location</th>
                    <th className="px-2 py-2">PIN</th>
                    <th className="px-2 py-2 text-right">Score</th>
                    <th className="px-2 py-2 text-right">Nearest own</th>
                    <th className="px-2 py-2 text-right">Catchment</th>
                    <th className="px-2 py-2">Cannibalization</th>
                  </tr>
                </thead>
                <tbody>
                  {locations.map((l, i) => (
                    <tr key={l.id} className="border-t border-[#EEF2F8]">
                      <td className="px-2 py-2 font-mono">{i + 1}</td>
                      <td className="px-2 py-2 font-medium">{l.name}</td>
                      <td className="px-2 py-2 font-mono">{l.pincode}</td>
                      <td className="px-2 py-2 text-right font-mono font-bold">{l.score}</td>
                      <td className="px-2 py-2 text-right font-mono">{formatKm(l.nearestOwnKm)}</td>
                      <td className="px-2 py-2 text-right font-mono">{formatNumber(l.catchmentPop)}</td>
                      <td className="px-2 py-2">{l.cannibalization.risk}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-[10px] text-slate-500">
                Branch placement and locality economics in this table are DEMO data generated for development.
              </p>
            </Section>
          )}

          <Section n="6" title="Risks & Considerations">
            <ul className="list-disc space-y-1 pl-5 text-sm">
              <li>Cannibalization: sites within 2 km of an existing own branch carry a HIGH risk penalty in the score.</li>
              <li>Market saturation: areas exceeding the configured branches-per-10k-population threshold are penalised.</li>
              <li>Digital substitution: high digital-readiness markets may warrant digital-first distribution over physical branches.</li>
              <li>Data granularity: PIN-level banking data is not published by RBI; locality figures are derived estimates.</li>
            </ul>
          </Section>

          <Section n="7" title="Recommendation">
            <p className="rounded-lg border border-[#1687F8]/30 bg-blue-50/50 p-3 text-sm leading-relaxed">{PRODUCT_PRINCIPLE}</p>
          </Section>

          <Section n="8" title="Methodology & Data Confidence">
            <p className="text-sm leading-relaxed">
              Location Opportunity Score = 0.15·Market Growth + 0.15·Credit Potential + 0.15·Deposit Potential +
              0.15·Customer Potential + 0.15·Bank Whitespace + 0.10·Competitive Opportunity + 0.05·Business/MSME +
              0.05·Accessibility + 0.05·Digital Readiness, less penalties for cannibalization risk, market saturation
              and operating cost. Weights and thresholds are server-side configuration. Official figures come from
              FY2025 annual reports; population and geography from Census/OpenStreetMap; branch placement and locality
              economics are clearly-labelled demo data.
            </p>
          </Section>

          <Section n="9" title="Disclaimer">
            <p className="text-xs leading-relaxed text-slate-500">
              BranchIQ provides analytical decision support based on publicly available information and its own models.
              It does not represent official recommendations from any bank or regulatory authority, and does not use
              confidential customer or internal bank data.
            </p>
          </Section>

          <div className="mt-8 border-t border-[#DFE7F0] pt-4 text-center text-[10px] text-slate-400">
            BRANCHIQ 2.0 · Branch Expansion Intelligence · Generated {today} · Public-data analytical estimate
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
