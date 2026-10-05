import { useMemo, useState } from "react";
import { ArrowUpDown, Trophy } from "lucide-react";

import { ChartCard, DataBadge, MethodologyNote, SectionTitle } from "@/components/shared/Ui";
import { useApp } from "@/context/AppContext";
import { useBanks } from "@/lib/branchiq";
import { formatCrore, formatNumber } from "@/lib/theme";
import type { Bank } from "@/types/api";

type Col = { key: keyof Bank; label: string; align?: "right"; fmt?: (v: never) => string };

const COLUMNS: Col[] = [
  { key: "short", label: "Bank" },
  { key: "sector", label: "Sector" },
  { key: "branches", label: "Branch Network", align: "right", fmt: ((v: number) => formatNumber(v)) as never },
  { key: "deposits", label: "Deposits", align: "right", fmt: ((v: number) => formatCrore(v)) as never },
  { key: "advances", label: "Advances", align: "right", fmt: ((v: number) => formatCrore(v)) as never },
  { key: "depositGrowth", label: "Dep. Growth", align: "right", fmt: ((v: number) => `${v}%`) as never },
  { key: "creditGrowth", label: "Credit Growth", align: "right", fmt: ((v: number) => `${v}%`) as never },
  { key: "digitalReadiness", label: "Digital", align: "right", fmt: ((v: number) => `${v}/100`) as never },
  { key: "geographicCoverage", label: "Coverage", align: "right", fmt: ((v: number) => `${v}/100`) as never },
];

export default function Comparison() {
  const { selectedBank, setSelectedBank } = useApp();
  const { data: banks } = useBanks();
  const [sortKey, setSortKey] = useState<keyof Bank>("branches");
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(() => {
    const rows = [...(banks ?? [])];
    rows.sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (typeof va === "string" && typeof vb === "string") return asc ? va.localeCompare(vb) : vb.localeCompare(va);
      return asc ? Number(va) - Number(vb) : Number(vb) - Number(va);
    });
    return rows;
  }, [banks, sortKey, asc]);

  const setSort = (k: keyof Bank) => {
    if (k === sortKey) setAsc(!asc);
    else {
      setSortKey(k);
      setAsc(false);
    }
  };

  const sectorAgg = ["Public", "Private"].map((sec) => {
    const items = (banks ?? []).filter((b) => b.sector === sec);
    const avg = (f: (b: Bank) => number) => (items.length ? Math.round(items.reduce((a, b) => a + f(b), 0) / items.length) : 0);
    return {
      sector: sec,
      banks: items.length,
      digital: avg((b) => b.digitalReadiness),
      coverage: avg((b) => b.geographicCoverage),
      depositGrowth: avg((b) => b.depositGrowth),
    };
  });

  return (
    <div className="space-y-8" data-testid="page-comparison">
      <SectionTitle
        eyebrow="Peer Benchmarking"
        title="Bank Comparison"
        subtitle="Compare all nine banks across official FY2025 metrics and BranchIQ analytical dimensions."
        testid="section-comparison"
      />

      <div className="bq-card bq-shadow overflow-hidden">
        <div className="bq-scroll overflow-x-auto">
          <table className="w-full text-sm" data-testid="comparison-table">
            <thead>
              <tr className="bg-[#071426] text-white">
                {COLUMNS.map((c) => (
                  <th
                    key={String(c.key)}
                    onClick={() => setSort(c.key)}
                    data-testid={`sort-${String(c.key)}`}
                    className={`cursor-pointer select-none whitespace-nowrap px-3 py-3 text-[11px] font-semibold uppercase tracking-wide ${
                      c.align === "right" ? "text-right" : "text-left"
                    }`}
                  >
                    <span className={`inline-flex items-center gap-1 ${c.align === "right" ? "flex-row-reverse" : ""}`}>
                      {c.label}
                      <ArrowUpDown size={11} className={sortKey === c.key ? "text-cyan-300" : "text-slate-500"} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r, i) => (
                <tr
                  key={r.id}
                  onClick={() => setSelectedBank(r.short)}
                  data-testid={`comparison-row-${i}`}
                  className={`cursor-pointer border-b border-[#EEF2F8] transition-colors ${
                    r.short === selectedBank ? "bg-blue-50" : "hover:bg-[#F4F7FB]"
                  }`}
                >
                  {COLUMNS.map((c) => {
                    const raw = r[c.key];
                    if (c.key === "short") {
                      return (
                        <td key="short" className="whitespace-nowrap px-3 py-3 font-semibold text-[#071426]">
                          <span className="flex items-center gap-1.5">
                            {i === 0 && !asc && <Trophy size={13} className="text-[#E79B24]" />}
                            {r.short}
                          </span>
                        </td>
                      );
                    }
                    if (c.key === "sector") {
                      return (
                        <td key="sector" className="px-3 py-3">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                              r.sector === "Public" ? "bg-cyan-50 text-cyan-700" : "bg-purple-50 text-purple-700"
                            }`}
                          >
                            {r.sector}
                          </span>
                        </td>
                      );
                    }
                    const text = c.fmt ? (c.fmt as (v: unknown) => string)(raw) : String(raw);
                    return (
                      <td
                        key={String(c.key)}
                        className={`whitespace-nowrap px-3 py-3 text-slate-700 ${c.align === "right" ? "text-right font-mono" : ""}`}
                      >
                        {text}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex flex-wrap items-center gap-2 border-t border-[#DFE7F0] bg-[#F4F7FB] px-3 py-2.5">
          <DataBadge type="official" />
          <span className="text-[10px] text-slate-500">
            Click any row to set the active bank · click headers to sort. Figures are official FY2025 disclosures.
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {sectorAgg.map((s) => (
          <ChartCard key={s.sector} title={`${s.sector} Sector — ${s.banks} banks`} badge={<DataBadge type="official" />} testid={`sector-card-${s.sector.toLowerCase()}`}>
            <div className="grid grid-cols-3 gap-3">
              {[
                ["Digital readiness", `${s.digital}/100`],
                ["Geographic coverage", `${s.coverage}/100`],
                ["Avg deposit growth", `${s.depositGrowth}%`],
              ].map(([l, v]) => (
                <div key={l} className="rounded-lg border border-[#DFE7F0] p-3 text-center">
                  <div className="stat-num text-xl text-[#071426]">{v}</div>
                  <div className="mt-1 text-[10px] text-slate-500">{l}</div>
                </div>
              ))}
            </div>
          </ChartCard>
        ))}
      </div>

      <MethodologyNote />
    </div>
  );
}
