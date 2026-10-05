import { ArrowRight, ChevronRight, Loader2, MapPin, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import GeospatialMap from "@/components/GeospatialMap";
import {
  ChartCard,
  ConfidenceBadge,
  DataBadge,
  DecisionBadge,
  EmptyState,
  MethodologyNote,
  RiskBadge,
  ScoreBar,
  ScoreRing,
  SectionTitle,
} from "@/components/shared/Ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useApp } from "@/context/AppContext";
import {
  useCitiesRanked,
  useDistrictsRanked,
  useLocationDetail,
  usePincodes,
  useRankedLocations,
  useStates,
} from "@/lib/branchiq";
import { PRODUCT_PRINCIPLE, TIER_LABELS, formatKm, formatNumber } from "@/lib/theme";

function Step({ n, label, done, active }: { n: number; label: string; done: boolean; active: boolean }) {
  return (
    <div className="flex items-center gap-2" data-testid={`drill-step-${n}`}>
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold transition-colors ${
          done ? "bg-emerald-500 text-white" : active ? "bg-[#1687F8] text-white" : "bg-slate-200 text-slate-500"
        }`}
      >
        {n}
      </span>
      <span className={`text-xs font-semibold ${active || done ? "text-[#071426]" : "text-slate-400"}`}>{label}</span>
    </div>
  );
}

export default function LocationIntelligence() {
  const {
    selectedBank,
    stateId,
    stateName,
    districtId,
    districtName,
    cityId,
    cityName,
    locationId,
    selectState,
    selectDistrict,
    selectCity,
    selectLocation,
  } = useApp();

  const [minScore, setMinScore] = useState<string>("");
  const [minPop, setMinPop] = useState<string>("");

  const { data: states } = useStates();
  const { data: districts, isLoading: dLoading } = useDistrictsRanked(stateId, selectedBank);
  const { data: cities, isLoading: cLoading } = useCitiesRanked(districtId, selectedBank);
  const { data: pins } = usePincodes(cityId);
  const filters = useMemo(
    () => ({ minScore: minScore ? Number(minScore) : null, minPopulation: minPop ? Number(minPop) : null, limit: 20 }),
    [minScore, minPop],
  );
  const {
    data: locations,
    isLoading: lLoading,
    isError: lError,
  } = useRankedLocations({ stateId, districtId, cityId }, selectedBank, filters);
  const { data: detail, isLoading: detailLoading } = useLocationDetail(locationId, selectedBank);

  // Auto-select the top candidate so the detail panel is never empty after a drill-down.
  useEffect(() => {
    if (locations && locations.length > 0 && !locations.some((l) => l.id === locationId)) {
      selectLocation(locations[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locations]);

  const center: [number, number] = detail
    ? [detail.lat, detail.lng]
    : locations && locations.length
      ? [locations[0].lat, locations[0].lng]
      : [22.5, 79.0];

  const stateList = states ?? [];

  return (
    <div className="space-y-6" data-testid="page-location-intelligence">
      <SectionTitle
        eyebrow="BranchIQ 2.0"
        title="Location Intelligence"
        subtitle="Drill from state to district, town/city, PIN code and candidate branch location — with transparent scores, geospatial whitespace and cannibalization analysis."
        right={<DataBadge type="analytical" />}
        testid="section-location-intelligence"
      />

      {/* Drill-down stepper + selectors */}
      <div className="bq-card bq-shadow p-4" data-testid="drilldown-panel">
        <div className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2">
          <Step n={1} label="Bank" done={!!selectedBank} active={false} />
          <ChevronRight size={14} className="text-slate-300" />
          <Step n={2} label="State" done={!!stateId} active={!stateId} />
          <ChevronRight size={14} className="text-slate-300" />
          <Step n={3} label="District" done={!!districtId} active={!!stateId && !districtId} />
          <ChevronRight size={14} className="text-slate-300" />
          <Step n={4} label="Town / City" done={!!cityId} active={!!districtId && !cityId} />
          <ChevronRight size={14} className="text-slate-300" />
          <Step n={5} label="Ranked locations" done={!!locationId} active={!!cityId} />
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <div>
            <div className="eyebrow mb-1">Step 2 · State</div>
            <Select
              value={stateId ?? ""}
              onValueChange={(v: string) => {
                const s = stateList.find((x) => x.id === v);
                selectState(v, s?.name ?? null);
              }}
            >
              <SelectTrigger data-testid="drilldown-state-select" className="h-9 w-[190px] border-[#DFE7F0] bg-white text-sm font-semibold">
                <SelectValue placeholder="Select state">
                  {(v) => stateList.find((x) => x.id === String(v))?.name ?? "Select state"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className="max-h-[320px]">
                {stateList.map((s) => (
                  <SelectItem key={s.id} value={s.id} data-testid={`state-option-${s.id}`}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <div className="eyebrow mb-1">Step 3 · District</div>
            <Select
              value={districtId ?? ""}
              onValueChange={(v: string) => {
                const d = (districts ?? []).find((x) => x.id === v);
                selectDistrict(v, d?.name ?? null);
              }}
            >
              <SelectTrigger
                data-testid="drilldown-district-select"
                className="h-9 w-[200px] border-[#DFE7F0] bg-white text-sm font-semibold"
                disabled={!stateId}
              >
                <SelectValue placeholder={stateId ? "Select district" : "Select state first"}>
                  {(v) => (districts ?? []).find((x) => x.id === String(v))?.name ?? "Select district"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className="max-h-[320px]">
                {(districts ?? []).map((d) => (
                  <SelectItem key={d.id} value={d.id} data-testid={`district-option-${d.name.toLowerCase().replace(/[^a-z]+/g, "-")}`}>
                    {d.name} · {d.overall}/100
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <div className="eyebrow mb-1">Step 4 · Town / City</div>
            <Select
              value={cityId ?? ""}
              onValueChange={(v: string) => {
                const c = (cities ?? []).find((x) => x.id === v);
                selectCity(v, c?.name ?? null);
              }}
            >
              <SelectTrigger
                data-testid="drilldown-city-select"
                className="h-9 w-[210px] border-[#DFE7F0] bg-white text-sm font-semibold"
                disabled={!districtId}
              >
                <SelectValue placeholder={districtId ? "Select town/city" : "Select district first"}>
                  {(v) => (cities ?? []).find((x) => x.id === String(v))?.name ?? "Select town/city"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className="max-h-[320px]">
                {(cities ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id} data-testid={`city-option-${c.name.toLowerCase().replace(/[^a-z]+/g, "-")}`}>
                    {c.name} · {c.overall}/100
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <div className="eyebrow mb-1">Min score</div>
            <Input
              data-testid="filter-min-score"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
              placeholder="0-100"
              className="h-9 w-[90px] border-[#DFE7F0] bg-white text-sm"
            />
          </div>
          <div>
            <div className="eyebrow mb-1">Min catchment</div>
            <Input
              data-testid="filter-min-population"
              value={minPop}
              onChange={(e) => setMinPop(e.target.value)}
              placeholder="e.g. 50000"
              className="h-9 w-[120px] border-[#DFE7F0] bg-white text-sm"
            />
          </div>
          <Button
            variant="outline"
            data-testid="btn-reset-drilldown"
            onClick={() => {
              selectState(null, null);
              setMinScore("");
              setMinPop("");
            }}
            className="h-9"
          >
            Reset
          </Button>
        </div>

        {/* Breadcrumb ribbon */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs" data-testid="drilldown-breadcrumb">
          <span className="rounded-md bg-[#071426] px-2 py-1 font-semibold text-white">{selectedBank}</span>
          {[stateName, districtName, cityName].filter(Boolean).map((n) => (
            <span key={n as string} className="flex items-center gap-1.5">
              <ChevronRight size={12} className="text-slate-300" />
              <span className="rounded-md border border-[#DFE7F0] bg-white px-2 py-1 font-medium text-slate-700">{n}</span>
            </span>
          ))}
          {!stateId && <span className="text-slate-400">— select a state to begin the drill-down</span>}
        </div>
      </div>

      {/* District rankings */}
      {stateId && (
        <ChartCard
          title={`Districts ranked — ${stateName} · ${selectedBank}`}
          eyebrow="Step 3"
          badge={<DataBadge type="analytical" />}
          testid="district-ranking-card"
        >
          {dLoading ? (
            <div className="py-6 text-center text-sm text-slate-400">
              <Loader2 className="mx-auto mb-2 animate-spin" size={18} /> Computing district opportunity…
            </div>
          ) : (
            <div className="bq-scroll max-h-[320px] overflow-auto">
              <Table data-testid="district-ranking-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>District</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead className="text-right">Pop (Mn)</TableHead>
                    <TableHead className="text-right">Own</TableHead>
                    <TableHead className="text-right">Competitors</TableHead>
                    <TableHead className="text-right">Score</TableHead>
                    <TableHead>Stance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(districts ?? []).map((d, i) => (
                    <TableRow
                      key={d.id}
                      onClick={() => selectDistrict(d.id, d.name)}
                      data-testid={`district-row-${i}`}
                      className={`cursor-pointer ${d.id === districtId ? "bg-blue-50" : "hover:bg-[#F4F7FB]"}`}
                    >
                      <TableCell className="font-mono text-xs text-slate-400">{i + 1}</TableCell>
                      <TableCell className="font-semibold text-[#071426]">{d.name}</TableCell>
                      <TableCell className="text-xs text-slate-500">{TIER_LABELS[d.tier] ?? d.tier}</TableCell>
                      <TableCell className="text-right font-mono">{d.populationMn}</TableCell>
                      <TableCell className="text-right font-mono">{d.ownBranches}</TableCell>
                      <TableCell className="text-right font-mono">{d.competitorBranches}</TableCell>
                      <TableCell className="text-right font-mono font-bold text-[#1687F8]">{d.overall}</TableCell>
                      <TableCell>
                        <DecisionBadge decision={d.decision} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </ChartCard>
      )}

      {/* City rankings */}
      {districtId && (
        <ChartCard
          title={`Towns & cities ranked — ${districtName}`}
          eyebrow="Step 4"
          badge={<DataBadge type="analytical" />}
          testid="city-ranking-card"
        >
          {cLoading ? (
            <div className="py-6 text-center text-sm text-slate-400">
              <Loader2 className="mx-auto mb-2 animate-spin" size={18} /> Computing town/city opportunity…
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(cities ?? []).map((c) => (
                <button
                  key={c.id}
                  onClick={() => selectCity(c.id, c.name)}
                  data-testid={`city-card-${c.name.toLowerCase().replace(/[^a-z]+/g, "-")}`}
                  className={`bq-card bq-card-hover p-3 text-left ${c.id === cityId ? "ring-2 ring-[#1687F8]" : ""}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-1.5 font-semibold text-[#071426]">
                        <MapPin size={13} className="text-[#1687F8]" />
                        {c.name}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        PIN {c.pin} · {c.kind} · {formatNumber(c.populationK)}k people
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="stat-num text-xl text-[#0F172A]">{c.overall}</div>
                      <div className="text-[9px] text-slate-400">Opportunity</div>
                    </div>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-1 text-[10px]">
                    <div>
                      <div className="text-slate-400">Whitespace</div>
                      <div className="stat-num text-[#071426]">{c.whitespace}</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Own</div>
                      <div className="stat-num text-[#071426]">{c.ownBranches}</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Nearest own</div>
                      <div className="stat-num text-[#071426]">{formatKm(c.nearestOwnKm)}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
          {cityId && pins && pins.length > 0 && (
            <div className="mt-3 rounded-lg border border-[#DFE7F0] bg-[#F8FAFC] p-3" data-testid="pincode-panel">
              <div className="eyebrow mb-1.5">Step 5 · PIN codes / localities in {cityName}</div>
              <div className="flex flex-wrap gap-1.5">
                {pins.map((p) => (
                  <span
                    key={p.id}
                    data-testid={`pincode-chip-${p.pin}`}
                    className="rounded-md border border-[#DFE7F0] bg-white px-2 py-1 text-[11px] text-slate-700"
                  >
                    <span className="font-mono font-semibold">{p.pin}</span> · {p.localityName}
                    <span className="ml-1 text-[9px] uppercase text-slate-400">({p.pinSource})</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </ChartCard>
      )}

      {/* Map + ranked candidate locations */}
      {(stateId || districtId || cityId) && (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          <div className="xl:col-span-7">
            <ChartCard
              title="Geospatial branch map"
              eyebrow="Step 6 · Candidate locations"
              badge={<DataBadge type="demo" />}
              testid="map-card"
            >
              <GeospatialMap
                center={center}
                candidates={locations ?? []}
                ownBranches={detail?.nearbyOwn ?? []}
                competitorBranches={detail?.nearbyCompetitors ?? []}
                catchmentRings={detail ? [1, 3, 5] : []}
                catchmentCenter={detail ? [detail.lat, detail.lng] : null}
                activeId={locationId}
                onSelectCandidate={selectLocation}
                height={420}
              />
            </ChartCard>
          </div>

          <div className="xl:col-span-5">
            <ChartCard
              title="Top candidate branch locations"
              eyebrow="Ranked by BranchIQ opportunity score"
              badge={<DataBadge type="analytical" />}
              testid="location-ranking-card"
            >
              {lLoading ? (
                <div className="py-6 text-center text-sm text-slate-400">
                  <Loader2 className="mx-auto mb-2 animate-spin" size={18} /> Running geospatial &amp; scoring engines…
                </div>
              ) : lError ? (
                <EmptyState title="Could not load locations" hint="The analytics service is unavailable." testid="locations-error" />
              ) : !locations || locations.length === 0 ? (
                <EmptyState
                  title="No candidate locations match the filters"
                  hint="Lower the minimum score or catchment threshold."
                  testid="locations-empty"
                />
              ) : (
                <div className="bq-scroll max-h-[420px] space-y-2 overflow-auto pr-1">
                  {locations.map((l, i) => (
                    <button
                      key={l.id}
                      onClick={() => selectLocation(l.id)}
                      data-testid={`candidate-location-card-${l.id.split("::").pop()}`}
                      className={`bq-card w-full p-3 text-left transition-colors ${
                        l.id === locationId ? "ring-2 ring-[#1687F8]" : "hover:bg-[#F8FAFC]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="flex h-5 w-5 items-center justify-center rounded bg-[#DBEAFE] font-mono text-[10px] font-bold text-[#1687F8]">
                              {i + 1}
                            </span>
                            <span className="truncate text-sm font-semibold text-[#071426]">{l.name}</span>
                          </div>
                          <div className="mt-0.5 text-[10px] text-slate-400">
                            {l.city} · {l.district} · PIN {l.pincode}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="stat-num text-lg text-[#0F172A]" data-testid={`ranked-branchiq-score-${i}`}>
                            {l.blended.branchIQScore}
                          </div>
                          <div className="text-[9px] text-slate-500">BranchIQ /100</div>
                        </div>
                      </div>
                      <div className="mt-2 grid grid-cols-3 gap-1 text-[10px]">
                        <div>
                          <div className="text-slate-500">Business</div>
                          <div className="stat-num" data-testid={`ranked-business-score-${i}`}>{l.score}</div>
                        </div>
                        <div>
                          <div className="text-slate-500">ML prob.</div>
                          <div className="stat-num" data-testid={`ranked-ml-probability-${i}`}>{l.mlProbability}%</div>
                        </div>
                        <div>
                          <div className="text-slate-500">Nearest own</div>
                          <div className="stat-num">{formatKm(l.nearestOwnKm)}</div>
                        </div>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        <DecisionBadge decision={l.decision} />
                        <RiskBadge risk={l.cannibalization.risk} />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </ChartCard>
          </div>
        </div>
      )}

      {/* Location detail */}
      {locationId && (
        <section className="bq-card bq-shadow p-5" data-testid="location-detail-panel">
          {detailLoading || !detail ? (
            <div className="py-8 text-center text-sm text-slate-400">
              <Loader2 className="mx-auto mb-2 animate-spin" size={18} /> Loading location detail…
            </div>
          ) : (
            <>
              <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="eyebrow">Location Detail</div>
                  <h3 className="font-display text-lg font-bold text-[#071426]">{detail.name}</h3>
                  <div className="text-xs text-slate-500">
                    {detail.city} · {detail.district} · {detail.state} · PIN {detail.pincode} · {detail.siteType}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <DataBadge type="analytical" />
                  <ConfidenceBadge level={detail.confidence.level} />
                  <DecisionBadge decision={detail.decision} />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr]">
                <div className="flex flex-col items-center gap-3">
                  <ScoreRing
                    value={detail.score}
                    size={180}
                    stroke={16}
                    color={detail.decision.color}
                    label="Location Opportunity"
                    sublabel={detail.priority}
                    testid="location-score-ring"
                  />
                  <div className="w-full rounded-lg bg-[#F4F7FB] p-3 text-center text-xs">
                    <div className="text-slate-500">
                      Base {detail.baseScore} − penalties {detail.totalPenalty} = <b className="text-[#071426]">{detail.score}</b>
                    </div>
                  </div>
                  {/* §19 — ML probability + business score + final blended BranchIQ score */}
                  <div className="w-full rounded-lg border border-[#DFE7F0] bg-white p-3" data-testid="blended-score-card">
                    <div className="eyebrow mb-2">Score triangulation</div>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div>
                        <div className="stat-num text-lg text-[#0F172A]" data-testid="blend-business-score">
                          {detail.blended.businessScore}
                        </div>
                        <div className="text-[9px] leading-tight text-slate-600">Business score</div>
                        <div className="text-[9px] text-slate-500">{Math.round(detail.blended.businessWeight * 100)}%</div>
                      </div>
                      <div>
                        <div className="stat-num text-lg text-fuchsia-700" data-testid="blend-ml-probability">
                          {detail.blended.mlProbability}%
                        </div>
                        <div className="text-[9px] leading-tight text-slate-600">ML probability</div>
                        <div className="text-[9px] text-slate-500">{Math.round(detail.blended.mlWeight * 100)}%</div>
                      </div>
                      <div>
                        <div className="stat-num text-lg text-[#1687F8]" data-testid="blend-branchiq-score">
                          {detail.blended.branchIQScore}
                        </div>
                        <div className="text-[9px] leading-tight text-slate-600">BranchIQ score</div>
                        <div
                          className={`text-[9px] font-semibold ${
                            detail.blended.delta > 0
                              ? "text-emerald-600"
                              : detail.blended.delta < 0
                                ? "text-rose-600"
                                : "text-slate-500"
                          }`}
                          data-testid="blend-delta"
                        >
                          {detail.blended.delta > 0 ? "+" : ""}
                          {detail.blended.delta}
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-center gap-1.5">
                      <DecisionBadge decision={detail.blended.decision} />
                    </div>
                    <div className="mt-2 text-[9px] leading-snug text-slate-600" data-testid="blend-note">
                      {detail.blended.note}
                    </div>
                  </div>
                  <div className="w-full rounded-lg border border-fuchsia-200 bg-fuchsia-50/60 p-3" data-testid="ml-prediction-card">
                    <div className="eyebrow mb-1 text-fuchsia-700">ML Prediction</div>
                    <div className="stat-num text-2xl text-[#071426]">{detail.mlPrediction.probability}%</div>
                    <div className="text-[10px] text-slate-500">probability of a high-potential branch market</div>
                    <div className="mt-2 space-y-1">
                      {detail.mlPrediction.contributions.slice(0, 4).map((c) => (
                        <div key={c.feature} className="flex items-center justify-between text-[10px]">
                          <span className="text-slate-600">{c.label}</span>
                          <span className={`stat-num ${c.contribution >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                            {c.contribution >= 0 ? "+" : ""}
                            {c.contributionPct}%
                          </span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-2 text-[9px] leading-snug text-slate-400">{detail.mlPrediction.note}</div>
                  </div>
                </div>

                <div className="space-y-5">
                  <div>
                    <div className="eyebrow mb-2">Score breakdown (transparent weights)</div>
                    <div className="grid grid-cols-1 gap-x-8 gap-y-3 sm:grid-cols-2">
                      {detail.breakdown.map((c) => (
                        <ScoreBar
                          key={c.key}
                          testid={`breakdown-${c.key}`}
                          label={`${c.label} · ×${c.weight}`}
                          value={c.score}
                          color="#1687F8"
                        />
                      ))}
                    </div>
                    {detail.penalties.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2" data-testid="penalties-list">
                        {detail.penalties.map((p) => (
                          <span
                            key={p.label}
                            className="rounded border border-rose-200 bg-rose-50 px-2 py-1 text-[11px] font-semibold text-rose-700"
                          >
                            {p.label}: −{p.penalty}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="rounded-lg border border-[#DFE7F0] p-3" data-testid="catchment-card">
                      <div className="eyebrow mb-2">Catchment analysis</div>
                      <table className="w-full text-[11px]">
                        <thead>
                          <tr className="text-left text-slate-400">
                            <th className="pb-1">Radius</th>
                            <th className="pb-1 text-right">Population</th>
                            <th className="pb-1 text-right">Own</th>
                            <th className="pb-1 text-right">Comp.</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.catchment.rings.map((r) => (
                            <tr key={r.radiusKm} className="border-t border-[#EEF2F8]">
                              <td className="py-1 font-semibold">{r.radiusKm} km</td>
                              <td className="py-1 text-right font-mono">{formatNumber(r.population)}</td>
                              <td className="py-1 text-right font-mono">{r.ownBranches}</td>
                              <td className="py-1 text-right font-mono">{r.competitorBranches}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="rounded-lg border border-[#DFE7F0] p-3" data-testid="cannibalization-card">
                      <div className="eyebrow mb-2">Whitespace &amp; cannibalization</div>
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Whitespace score</span>
                          <span className="stat-num text-[#071426]">{detail.whitespaceScore}/100</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Nearest own branch</span>
                          <span className="stat-num">{formatKm(detail.nearestOwnKm)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Nearest competitor</span>
                          <span className="stat-num">{formatKm(detail.nearestCompetitorKm)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Branches / 10k pop</span>
                          <span className="stat-num">{detail.branchesPer10kPop}</span>
                        </div>
                        <RiskBadge risk={detail.cannibalization.risk} />
                        <p className="text-[10px] leading-snug text-slate-500">{detail.cannibalization.note}</p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#1687F8]/30 bg-blue-50/50 p-4" data-testid="why-this-location">
                    <div className="eyebrow mb-2 flex items-center gap-1.5 text-[#1687F8]">
                      <Sparkles size={13} /> Why this location?
                    </div>
                    <ul className="space-y-1.5">
                      {detail.evidence.map((e, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-slate-700">
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1687F8]" />
                          <span>
                            {e.text}
                            <span className="ml-1 rounded bg-white px-1 py-0.5 text-[9px] font-semibold text-slate-500">
                              {e.type}
                            </span>
                          </span>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-3 border-t border-blue-200 pt-2 text-[11px] font-medium text-[#071426]">
                      {PRODUCT_PRINCIPLE}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="rounded-lg border border-[#DFE7F0] p-3" data-testid="nearby-own-list">
                      <div className="eyebrow mb-2">Nearest {selectedBank} branches</div>
                      {detail.nearbyOwn.length === 0 ? (
                        <p className="text-[11px] text-slate-400">None recorded within 10 km — full whitespace.</p>
                      ) : (
                        <ul className="space-y-1 text-[11px]">
                          {detail.nearbyOwn.slice(0, 5).map((b) => (
                            <li key={b.id} className="flex items-center justify-between gap-2">
                              <span className="truncate text-slate-600">{b.name}</span>
                              <span className="stat-num shrink-0 text-[#071426]">{b.distanceKm} km</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div className="rounded-lg border border-[#DFE7F0] p-3" data-testid="nearby-competitors-list">
                      <div className="eyebrow mb-2">Nearest competitor branches</div>
                      <ul className="space-y-1 text-[11px]">
                        {detail.nearbyCompetitors.slice(0, 5).map((b) => (
                          <li key={b.id} className="flex items-center justify-between gap-2">
                            <span className="truncate text-slate-600">
                              <b>{b.bankShort}</b> — {b.name}
                            </span>
                            <span className="stat-num shrink-0 text-[#071426]">{b.distanceKm} km</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3" data-testid="data-provenance">
                    <div className="eyebrow mb-1.5 text-amber-800">Data confidence &amp; sources</div>
                    <div className="mb-2 flex flex-wrap gap-1.5">
                      <ConfidenceBadge level={detail.confidence.level} />
                      <DataBadge type="demo" />
                      <DataBadge type="market" />
                    </div>
                    <p className="text-[10px] leading-snug text-slate-600">
                      Market indicators used: {detail.marketSource}. {detail.confidence.notes.join(" ")}
                    </p>
                  </div>

                  <a
                    href="/consultant"
                    data-testid="ask-consultant-link"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-[#1687F8] hover:underline"
                  >
                    Ask the AI Consultant about this location <ArrowRight size={14} />
                  </a>
                </div>
              </div>
            </>
          )}
        </section>
      )}

      <MethodologyNote />
    </div>
  );
}
