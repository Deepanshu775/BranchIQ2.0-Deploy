// TanStack Query hooks over the typed /api fetch layer. Every heavy calculation
// (geospatial, scoring, ML) happens server-side; these hooks only fetch results.
import { useQuery } from "@tanstack/react-query";

import { apiGet } from "@/lib/api";
import type {
  Bank,
  BranchPage,
  City,
  CityRanked,
  CompetitorsNear,
  District,
  DistrictRanked,
  LocationDetail,
  MarketOverview,
  ModelInfo,
  Pincode,
  QualityReport,
  RankedLocation,
  SourcesResponse,
  StateGeo,
  StateRanked,
  TrainingDataSummary,
} from "@/types/api";

const qs = (params: Record<string, string | number | null | undefined>) => {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== "") sp.set(k, String(v));
  });
  const s = sp.toString();
  return s ? `?${s}` : "";
};

export const useBanks = () =>
  useQuery({ queryKey: ["banks"], queryFn: () => apiGet<Bank[]>("/banks"), staleTime: 600_000 });

export const useStates = () =>
  useQuery({ queryKey: ["states"], queryFn: () => apiGet<StateGeo[]>("/states"), staleTime: 600_000 });

export const useDistricts = (stateId: string | null) =>
  useQuery({
    queryKey: ["districts", stateId],
    queryFn: () => apiGet<District[]>(`/districts${qs({ state_id: stateId })}`),
    enabled: !!stateId,
    staleTime: 600_000,
  });

export const useCities = (districtId: string | null) =>
  useQuery({
    queryKey: ["cities", districtId],
    queryFn: () => apiGet<City[]>(`/cities${qs({ district_id: districtId })}`),
    enabled: !!districtId,
    staleTime: 600_000,
  });

export const usePincodes = (cityId: string | null) =>
  useQuery({
    queryKey: ["pincodes", cityId],
    queryFn: () => apiGet<Pincode[]>(`/pincodes${qs({ city_id: cityId })}`),
    enabled: !!cityId,
    staleTime: 600_000,
  });

export const useStatesRanked = (bank: string) =>
  useQuery({
    queryKey: ["opp-states", bank],
    queryFn: () => apiGet<StateRanked[]>(`/opportunities/states${qs({ bank })}`),
    staleTime: 120_000,
  });

export const useDistrictsRanked = (stateId: string | null, bank: string) =>
  useQuery({
    queryKey: ["opp-districts", stateId, bank],
    queryFn: () => apiGet<DistrictRanked[]>(`/opportunities/districts${qs({ state_id: stateId, bank })}`),
    enabled: !!stateId,
    staleTime: 120_000,
  });

export const useCitiesRanked = (districtId: string | null, bank: string) =>
  useQuery({
    queryKey: ["opp-cities", districtId, bank],
    queryFn: () => apiGet<CityRanked[]>(`/opportunities/cities${qs({ district_id: districtId, bank })}`),
    enabled: !!districtId,
    staleTime: 120_000,
  });

export interface LocationFilters {
  minScore?: number | null;
  minPopulation?: number | null;
  limit?: number;
}

export const useRankedLocations = (
  scope: { stateId?: string | null; districtId?: string | null; cityId?: string | null },
  bank: string,
  filters: LocationFilters = {},
) => {
  const enabled = !!(scope.cityId || scope.districtId || scope.stateId);
  return useQuery({
    queryKey: ["ranked-locations", scope.stateId, scope.districtId, scope.cityId, bank, filters],
    queryFn: () =>
      apiGet<RankedLocation[]>(
        `/locations/ranked${qs({
          state_id: scope.stateId,
          district_id: scope.districtId,
          city_id: scope.cityId,
          bank,
          min_score: filters.minScore,
          min_population: filters.minPopulation,
          limit: filters.limit ?? 20,
        })}`,
      ),
    enabled,
    staleTime: 60_000,
  });
};

export const useLocationDetail = (locationId: string | null, bank: string) =>
  useQuery({
    queryKey: ["location-detail", locationId, bank],
    queryFn: () => apiGet<LocationDetail>(`/location/${encodeURIComponent(locationId!)}${qs({ bank })}`),
    enabled: !!locationId,
    staleTime: 60_000,
  });

export const useBranches = (
  scope: { bank?: string; stateId?: string | null; districtId?: string | null; cityId?: string | null },
  limit = 300,
) =>
  useQuery({
    queryKey: ["branches", scope, limit],
    queryFn: () =>
      apiGet<BranchPage>(
        `/branches${qs({
          bank: scope.bank,
          state_id: scope.stateId,
          district_id: scope.districtId,
          city_id: scope.cityId,
          limit,
        })}`,
      ),
    enabled: !!(scope.districtId || scope.cityId || scope.stateId),
    staleTime: 300_000,
  });

export const useCompetitors = (lat: number | null, lng: number | null, radiusKm: number, excludeBank: string) =>
  useQuery({
    queryKey: ["competitors", lat, lng, radiusKm, excludeBank],
    queryFn: () =>
      apiGet<CompetitorsNear>(
        `/competitors${qs({ lat, lng, radius_km: radiusKm, exclude_bank: excludeBank })}`,
      ),
    enabled: lat !== null && lng !== null,
    staleTime: 120_000,
  });

export const useMarketOverview = (districtId: string | null) =>
  useQuery({
    queryKey: ["market", districtId],
    queryFn: () => apiGet<MarketOverview>(`/market/${encodeURIComponent(districtId!)}`),
    enabled: !!districtId,
    staleTime: 120_000,
  });

export const useSources = () =>
  useQuery({ queryKey: ["sources"], queryFn: () => apiGet<SourcesResponse>("/sources"), staleTime: 600_000 });

export const useQualityReport = () =>
  useQuery({ queryKey: ["quality"], queryFn: () => apiGet<QualityReport>("/quality"), staleTime: 300_000 });

export const useModelInfo = () =>
  useQuery({ queryKey: ["model-info"], queryFn: () => apiGet<ModelInfo>("/model/info"), staleTime: 60_000 });

export const useTrainingData = () =>
  useQuery({
    queryKey: ["model-training-data"],
    queryFn: () => apiGet<TrainingDataSummary>("/model/training-data"),
    staleTime: 60_000,
  });
