import { AlertTriangle, CheckCircle2, Database, ExternalLink, ShieldCheck } from "lucide-react";

import { ConfidenceBadge, DataBadge, MethodologyNote, SectionTitle } from "@/components/shared/Ui";
import { useBanks, useQualityReport, useSources } from "@/lib/branchiq";

const TYPE_BADGE: Record<string, string> = {
  official: "official",
  market: "market",
  analytical: "analytical",
  model: "prediction",
  demo: "demo",
};

export default function Methodology() {
  const { data: sources } = useSources();
  const { data: quality } = useQualityReport();
  const { data: banks } = useBanks();

  const registry = sources?.sources ?? [];
  const cfg = sources?.scoringConfig;
  const issues = quality?.issues ?? {};
  const totalIssues = Object.values(issues).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-8" data-testid="page-methodology">
      <SectionTitle
        eyebrow="Transparency"
        title="Data Registry & Methodology"
        subtitle="Every metric is classified by origin — official, public market, BranchIQ derived, model estimate, ML prediction or demo."
        testid="section-methodology"
      />

      <div className="rounded-lg border border-amber-300 bg-amber-50 p-4" data-testid="demo-disclaimer">
        <div className="mb-1.5 flex items-center gap-2">
          <AlertTriangle size={16} className="text-amber-700" />
          <h3 className="font-display text-sm font-bold text-amber-900">What is real and what is demo data</h3>
        </div>
        <ul className="space-y-1 text-xs leading-relaxed text-amber-900">
          <li>• <b>Official reported data:</b> bank branch totals, deposits, advances and growth (FY2025 annual reports).</li>
          <li>• <b>Public market data:</b> state/district/town names, populations and approximate coordinates (Census, OpenStreetMap).</li>
          <li>• <b>DEMO data:</b> individual branch placement, PIN-locality economics and candidate sites are synthetic, generated deterministically for development — never official bank data.</li>
          <li>• <b>BranchIQ analytical / ML:</b> opportunity, whitespace, cannibalization scores and the high-potential probability are BranchIQ's own model output, not regulator or bank recommendations.</li>
        </ul>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {registry.map((s) => (
          <div key={s.sourceId} data-testid={`source-card-${s.sourceId}`} className="bq-card bq-shadow p-5">
            <div className="mb-2 flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#071426] text-white">
                <Database size={18} />
              </span>
              <h3 className="font-display text-sm font-bold leading-tight text-[#071426]">{s.sourceName}</h3>
            </div>
            <p className="mb-2 text-xs text-slate-500">{s.organization}</p>
            <div className="mb-2 flex flex-wrap gap-1.5">
              <DataBadge type={TYPE_BADGE[s.dataType] ?? "model"} />
              <ConfidenceBadge level={s.confidence.toUpperCase()} />
            </div>
            <div className="eyebrow mb-1.5">Used For</div>
            <div className="flex flex-wrap gap-1.5">
              {s.usedFor.map((u) => (
                <span key={u} className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-[11px] text-slate-600">
                  {u}
                </span>
              ))}
            </div>
            <div className="mt-2 text-[10px] text-slate-400">
              Dataset: {s.dataset} · Period: {s.period}
            </div>
            {s.url && (
              <a
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-[#1687F8] hover:underline"
              >
                Open source <ExternalLink size={11} />
              </a>
            )}
          </div>
        ))}
      </div>

      {/* Data quality dashboard (§31) */}
      <section className="bq-card bq-shadow p-5" data-testid="data-quality-dashboard">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-lg font-bold text-[#071426]">Data Quality Dashboard</h3>
          {totalIssues === 0 ? (
            <span className="inline-flex items-center gap-1.5 rounded border border-emerald-300 bg-emerald-50 px-2 py-1 text-[11px] font-bold text-emerald-700">
              <CheckCircle2 size={12} /> ALL CHECKS PASSED
            </span>
          ) : (
            <span className="rounded border border-amber-300 bg-amber-50 px-2 py-1 text-[11px] font-bold text-amber-700">
              {totalIssues} ISSUES FOUND
            </span>
          )}
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
          {[
            ["Branch records", quality?.branchCount ?? 0, false],
            ["PIN areas", quality?.pinAreaCount ?? 0, false],
            ["Invalid coordinates", issues.invalidCoordinates ?? 0, true],
            ["Invalid PIN codes", issues.invalidPincodes ?? 0, true],
            ["Missing district", issues.missingDistrict ?? 0, true],
            ["Duplicate branches", issues.duplicateBranches ?? 0, true],
            ["Stale records", issues.staleRecords ?? 0, true],
          ].map(([label, value, isIssue]) => (
            <div
              key={label as string}
              data-testid={`quality-metric-${String(label).toLowerCase().replace(/[^a-z]+/g, "-")}`}
              className={`rounded-lg border p-3 text-center ${
                isIssue && Number(value) > 0 ? "border-rose-200 bg-rose-50" : "border-[#DFE7F0]"
              }`}
            >
              <div className={`stat-num text-xl ${isIssue && Number(value) > 0 ? "text-rose-700" : "text-[#071426]"}`}>
                {Number(value).toLocaleString("en-IN")}
              </div>
              <div className="mt-1 text-[10px] text-slate-500">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Scoring formula */}
      {cfg && (
        <section className="bq-card bq-shadow p-5" data-testid="scoring-config-panel">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-display text-lg font-bold text-[#071426]">
              How the Location Opportunity Score is calculated
            </h3>
            <DataBadge type="analytical" />
          </div>
          <p className="mb-3 text-xs text-slate-500">
            Weights and thresholds are stored in server-side configuration (not hard-coded in the UI) so they can be
            re-tuned without a code change.
          </p>
          <div className="space-y-2.5">
            {Object.entries(cfg.location_score_weights).map(([k, w]) => (
              <div key={k} className="flex items-center gap-3">
                <span className="w-48 text-sm capitalize text-slate-600">{k.replace(/([A-Z])/g, " $1")}</span>
                <span className="w-14 font-mono text-xs text-slate-400">×{w}</span>
                <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-[#1687F8]" style={{ width: `${w * 100 * 5}%` }} />
                </div>
                <span className="w-12 text-right font-mono text-xs font-semibold text-[#0C1D33]">
                  {Math.round(w * 100)}%
                </span>
              </div>
            ))}
          </div>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-[#DFE7F0] p-3">
              <div className="eyebrow mb-2">Decision bands (configurable)</div>
              <ul className="space-y-1 text-xs">
                {cfg.decision_bands.map((b) => (
                  <li key={b.label} className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: b.color }} />
                    <span className="font-mono text-[11px] text-slate-400">{b.min}+</span>
                    <span className="text-slate-700">{b.label}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-[#DFE7F0] p-3">
              <div className="eyebrow mb-2">Cannibalization bands (configurable)</div>
              <ul className="space-y-1 text-xs">
                {cfg.cannibalization_bands_km.map((b) => (
                  <li key={b.risk} className="flex items-center justify-between">
                    <span className="text-slate-700">
                      Own branch &lt; {b.max_km > 100 ? "∞" : `${b.max_km} km`} → <b>{b.risk}</b>
                    </span>
                    <span className="font-mono text-[11px] text-rose-600">−{b.penalty}</span>
                  </li>
                ))}
              </ul>
              <div className="eyebrow mb-1 mt-3">Catchment radii</div>
              <p className="font-mono text-xs text-slate-600">{cfg.catchment_radii_km.join(" / ")} km</p>
            </div>
          </div>
        </section>
      )}

      {/* Bank annual report links */}
      <section className="bq-card bq-shadow p-5" data-testid="section-annual-reports">
        <div className="mb-1 flex items-center justify-between">
          <h3 className="font-display text-lg font-bold text-[#071426]">Official Bank Annual Reports</h3>
          <DataBadge type="official" />
        </div>
        <p className="mb-4 text-xs text-slate-500">
          Direct links to each bank's official investor-relations page (FY2025). Reported figures are attributed to
          these public disclosures.
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(banks ?? []).map((b) => (
            <a
              key={b.id}
              href={b.sourceUrl}
              target="_blank"
              rel="noreferrer"
              data-testid={`annual-report-link-${b.id}`}
              className="group flex items-center gap-3 rounded-lg border border-[#DFE7F0] bg-white px-3 py-2.5 transition-colors hover:border-[#1687F8] hover:bg-blue-50/40"
            >
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold text-[#071426]">{b.short}</span>
                <span className="block text-[10px] uppercase tracking-wide text-slate-400">
                  {b.sector} Sector · {b.reportingPeriod}
                </span>
              </span>
              <ExternalLink size={14} className="text-slate-300 transition-colors group-hover:text-[#1687F8]" />
            </a>
          ))}
        </div>
      </section>

      <section className="bq-card bq-shadow p-5" style={{ background: "linear-gradient(120deg,#071426,#0C1D33)" }}>
        <div className="mb-3 flex items-center gap-2 text-white">
          <ShieldCheck size={18} className="text-cyan-300" />
          <h3 className="font-display text-lg font-bold">Transparency &amp; Data Integrity</h3>
        </div>
        <ul className="mb-4 space-y-2">
          {[
            "BranchIQ does not use confidential customer or internal bank data.",
            "Opportunity, whitespace and cannibalization scores are BranchIQ analytical estimates, not official figures.",
            "PIN-level banking data is not published by RBI — PIN/locality recommendations are derived from district/city indicators plus geospatial branch data.",
            "BranchIQ never states that a regulator recommends opening a branch; it flags locations for further feasibility evaluation.",
          ].map((t) => (
            <li key={t} className="flex items-start gap-2 text-sm text-slate-200">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400" />
              {t}
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400">Confidence levels applied across recommendations:</span>
          <ConfidenceBadge level="HIGH" />
          <ConfidenceBadge level="MEDIUM" />
          <ConfidenceBadge level="LIMITED" />
        </div>
      </section>

      <MethodologyNote />
    </div>
  );
}
