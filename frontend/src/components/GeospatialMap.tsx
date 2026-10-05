// Leaflet geospatial engine panel. Markers: selected-bank branches, competitor branches,
// candidate locations colour-coded by opportunity (green/amber/red, grey = insufficient data).
import L from "leaflet";
import { useEffect, useRef } from "react";

import { MARKER, markerColor } from "@/lib/theme";
import type { NearbyBranch, RankedLocation } from "@/types/api";

export interface MapBranch {
  id: string;
  bankShort: string;
  name: string;
  lat: number;
  lng: number;
  pincode?: string;
  distanceKm?: number;
}

interface Props {
  center: [number, number];
  zoom?: number;
  ownBranches?: MapBranch[] | NearbyBranch[];
  competitorBranches?: MapBranch[] | NearbyBranch[];
  candidates?: RankedLocation[];
  catchmentRings?: number[];
  catchmentCenter?: [number, number] | null;
  activeId?: string | null;
  onSelectCandidate?: (id: string) => void;
  height?: number;
  testid?: string;
}

function pinIcon(color: string, size: number, pulse = false, label?: string) {
  return L.divIcon({
    className: "",
    html: `<div class="bq-pin${pulse ? " bq-marker-pulse" : ""}" style="width:${size}px;height:${size}px;background:${color};color:${color}">
             ${label ? `<span style="color:#fff;font-size:${Math.round(size * 0.46)}px;font-weight:700;font-family:'JetBrains Mono Variable',monospace">${label}</span>` : ""}
           </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function GeospatialMap({
  center,
  zoom = 11,
  ownBranches = [],
  competitorBranches = [],
  candidates = [],
  catchmentRings = [],
  catchmentCenter = null,
  activeId = null,
  onSelectCandidate,
  height = 460,
  testid = "geospatial-map",
}: Props) {
  const nodeRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const onSelectRef = useRef(onSelectCandidate);
  onSelectRef.current = onSelectCandidate;

  // Create the map once; StrictMode double-invokes effects, so creation is guarded.
  useEffect(() => {
    if (!nodeRef.current || mapRef.current) return;
    const map = L.map(nodeRef.current, { zoomControl: true, attributionControl: true }).setView(center, zoom);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-draw markers whenever the data or selection changes.
  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();

    const ringCenter = catchmentCenter ?? center;
    catchmentRings.forEach((r) => {
      L.circle(ringCenter, {
        radius: r * 1000,
        color: "#1687F8",
        weight: 1,
        opacity: 0.45,
        fillColor: "#1687F8",
        fillOpacity: 0.05,
      })
        .bindTooltip(`${r} km catchment`, { sticky: true })
        .addTo(layer);
    });

    competitorBranches.forEach((b) => {
      L.marker([b.lat, b.lng], { icon: pinIcon(MARKER.competitor, 13) })
        .bindPopup(
          `<b>${b.bankShort}</b> — competitor<br/>${b.name}` +
            (b.distanceKm !== undefined ? `<br/>${b.distanceKm} km away` : ""),
        )
        .addTo(layer);
    });

    ownBranches.forEach((b) => {
      L.marker([b.lat, b.lng], { icon: pinIcon(MARKER.ownBranch, 16) })
        .bindPopup(
          `<b>${b.bankShort}</b> — own branch<br/>${b.name}` +
            (b.distanceKm !== undefined ? `<br/>${b.distanceKm} km away` : ""),
        )
        .addTo(layer);
    });

    candidates.forEach((c, i) => {
      const active = activeId === c.id;
      const marker = L.marker([c.lat, c.lng], {
        icon: pinIcon(markerColor(c.score), active ? 32 : 26, active, String(i + 1)),
        zIndexOffset: active ? 1000 : 500,
      })
        .bindPopup(
          `<b>${c.name}</b><br/>Score <b>${c.score}</b>/100 · ${c.decision.label}<br/>` +
            `PIN ${c.pincode} · catchment ${c.catchmentPop.toLocaleString("en-IN")}<br/>` +
            `Cannibalization: ${c.cannibalization.risk}`,
        )
        .addTo(layer);
      marker.on("click", () => onSelectRef.current?.(c.id));
    });

    const pts: [number, number][] = [
      ...candidates.map((c) => [c.lat, c.lng] as [number, number]),
      ...ownBranches.map((b) => [b.lat, b.lng] as [number, number]),
      ...competitorBranches.slice(0, 40).map((b) => [b.lat, b.lng] as [number, number]),
    ];
    if (pts.length > 1) {
      map.fitBounds(L.latLngBounds(pts).pad(0.22), { animate: true });
    } else {
      map.setView(center, zoom, { animate: true });
    }
  }, [center, zoom, ownBranches, competitorBranches, candidates, catchmentRings, catchmentCenter, activeId]);

  return (
    <div className="relative overflow-hidden rounded-[14px] border border-[#DFE7F0]" data-testid={testid}>
      <div ref={nodeRef} style={{ height }} />
      <div
        className="pointer-events-none absolute bottom-3 left-3 z-[500] rounded-lg border border-[#DFE7F0] bg-white/95 px-3 py-2 text-[10px] shadow-sm backdrop-blur"
        data-testid="map-legend"
      >
        <div className="eyebrow mb-1.5">Legend</div>
        {[
          ["#16A36A", "Candidate — high opportunity (80+)"],
          ["#E79B24", "Candidate — medium (65–79)"],
          ["#D9534F", "Candidate — low (<65)"],
          [MARKER.ownBranch, "Selected bank branch"],
          [MARKER.competitor, "Competitor branch"],
          [MARKER.insufficient, "Insufficient data"],
        ].map(([color, label]) => (
          <div key={label} className="flex items-center gap-1.5 leading-5">
            <span className="h-2.5 w-2.5 rounded-full border border-white shadow" style={{ background: color }} />
            <span className="text-slate-600">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
