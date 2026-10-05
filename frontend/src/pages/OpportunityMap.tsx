import { MapPin } from "lucide-react";

import GeospatialMap from "@/components/GeospatialMap";
import { ChartCard, DataBadge, DecisionBadge, MethodologyNote, SectionTitle } from "@/components/shared/Ui";
import { useApp } from "@/context/AppContext";
import { useRankedLocations, useStates, useStatesRanked } from "@/lib/branchiq";
import { opportunityFill, opportunityText } from "@/lib/theme";

export default function OpportunityMap() {
  const { selectedBank, stateId, selectState, locationId, selectLocation } = useApp();
  const { data: rows } = useStatesRanked(selectedBank);
  const { data: states } = useStates();
  const { data: locations } = useRankedLocations({ stateId }, selectedBank, { limit: 15 });

  const data = rows ?? [];
  const active = data.find((d) => d.id === stateId) ?? data[0];
  const stateGeo = (states ?? []).find((s) => s.id === (stateId ?? active?.id));
  const center: [number, number] = stateGeo ? [stateGeo.lat, stateGeo.lng] : [22.5, 79.0];

  return (
    <div className="space-y-6" data-testid="page-opportunity-map">
      <SectionTitle
        eyebrow="Regional Intelligence"
        title="Opportunity Map"
        subtitle={`Where should ${selectedBank} expand next? Click a state tile to load its candidate branch locations on the map.`}
        right={<DataBadge type="analytical" />}
        testid="section-opportunity-map"
      />

      <div className="bq-card bq-shadow p-5">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_300px]" data-testid="opportunity-heatmap">
          <div>
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 xl:grid-cols-4">
              {data.map((r) => (
                <button
                  key={r.id}
                  onClick={() => selectState(r.id, r.state)}
                  data-testid={`heat-tile-${r.id}`}
                  className={`rounded-xl p-3 text-left transition-transform hover:-translate-y-0.5 ${
                    active?.id === r.id ? "ring-2 ring-offset-2 ring-[#111827]" : ""
                  }`}
                  style={{ background: opportunityFill(r.score), color: opportunityText(r.score) }}
                >
                  <div className="text-xs font-semibold leading-tight">{r.state}</div>
                  <div className="stat-num mt-1 text-xl">{r.score}</div>
                  <div className="text-[10px] opacity-80">{r.region} Region</div>
                </button>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wide text-slate-400">Low</span>
              {["#DBEAFE", "#67E8F9", "#0891B2", "#2563EB", "#1D4ED8"].map((c) => (
                <span key={c} className="h-3 w-8 rounded-sm" style={{ background: c }} />
              ))}
              <span className="text-[10px] uppercase tracking-wide text-slate-400">High</span>
            </div>
          </div>

          {active && (
            <div className="bq-card h-fit p-4" data-testid="heatmap-detail">
              <div className="flex items-center gap-1.5 font-semibold text-[#0F172A]">
                <MapPin size={15} className="text-[#1687F8]" />
                {active.state}
              </div>
              <div className="mt-3 flex items-end gap-2">
                <span className="stat-num text-4xl text-[#0F172A]">{active.score}</span>
                <span className="mb-1.5 text-xs text-slate-400">Opportunity / 100</span>
              </div>
              <div className="mt-3 space-y-1.5 text-xs">
                {Object.entries(active.sub).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between">
                    <span className="capitalize text-slate-500">{k.replace(/([A-Z])/g, " $1")}</span>
                    <span className="stat-num text-[#0F172A]">{v}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 border-t border-[#E2E8F0] pt-3">
                <div className="eyebrow mb-1">Recommendation</div>
                <DecisionBadge decision={active.decision} />
                <p className="mt-2 text-xs leading-relaxed text-slate-600">{active.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <ChartCard
        title={`Candidate locations — ${active?.state ?? "select a state"}`}
        eyebrow="Geospatial drill-down"
        badge={<DataBadge type="demo" />}
        testid="opportunity-map-card"
      >
        <GeospatialMap
          center={center}
          zoom={7}
          candidates={locations ?? []}
          activeId={locationId}
          onSelectCandidate={selectLocation}
          height={440}
          testid="state-geospatial-map"
        />
        {!stateId && (
          <p className="mt-2 text-xs text-slate-400">
            Select a state tile above to plot its top-ranked candidate branch locations.
          </p>
        )}
      </ChartCard>

      <MethodologyNote />
    </div>
  );
}
