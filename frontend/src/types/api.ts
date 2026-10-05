// Hand-written TS mirrors of the Pydantic models in backend/models/models.py.
// Nothing infers across the HTTP boundary — change a model, change its interface in the same edit.

export interface Bank {
  id: string;
  short: string;
  name: string;
  sector: string;
  reportingPeriod: string;
  branches: number;
  deposits: number;
  advances: number;
  depositGrowth: number;
  creditGrowth: number;
  digitalReadiness: number;
  geographicCoverage: number;
  footprintWeight: number;
  source: string;
  sourceUrl: string;
}

export interface StateIndicators {
  gsdpGrowth: number;
  marketGrowth: number;
  creditOpportunity: number;
  depositOpportunity: number;
  customerPotential: number;
  digitalReadiness: number;
  marketConcentration: number;
  dataConfidence: string;
}

export interface StateGeo {
  id: string;
  name: string;
  region: string;
  lat: number;
  lng: number;
  populationMn: number;
  indicators: StateIndicators;
}

export interface District {
  id: string;
  stateId: string;
  state: string;
  name: string;
  lat: number;
  lng: number;
  populationMn: number;
  tier: string;
}

export interface City {
  id: string;
  stateId: string;
  districtId: string;
  name: string;
  lat: number;
  lng: number;
  populationK: number;
  pin: string;
  kind: string;
  tier: string;
}

export interface Pincode {
  id: string;
  pin: string;
  cityId: string;
  districtId: string;
  stateId: string;
  localityName: string;
  lat: number;
  lng: number;
  catchmentPopK: number;
  pinSource: string;
}

export interface Branch {
  id: string;
  bankId: string;
  bankShort: string;
  bankName: string;
  name: string;
  code: string;
  stateId: string;
  districtId: string;
  cityId: string;
  city: string;
  pincode: string;
  lat: number;
  lng: number;
  branchType: string;
  openingDate: string;
  sourceType: string;
  status: string;
  lastVerified: string;
}

export interface BranchPage {
  total: number;
  items: Branch[];
}

export interface Decision {
  label: string;
  color: string;
}

export interface Cannibalization {
  risk: string;
  penalty: number;
  nearestOwnKm: number | null;
  note: string;
}

export interface Driver {
  key: string;
  label: string;
  value: number;
}

export interface StateRanked {
  id: string;
  state: string;
  region: string;
  populationMn: number;
  score: number;
  sub: Record<string, number>;
  presence: number;
  decision: Decision;
  priority: string;
  drivers: Driver[];
  recommendation: string;
  dataConfidence: string;
}

export interface DistrictRanked {
  id: string;
  stateId: string;
  state: string;
  name: string;
  tier: string;
  populationMn: number;
  ownBranches: number;
  totalBranches: number;
  competitorBranches: number;
  penetrationPct: number;
  sub: Record<string, number>;
  overall: number;
  decision: Decision;
  priority: string;
  drivers: Driver[];
  dataConfidence: string;
}

export interface CityRanked {
  id: string;
  districtId: string;
  district: string;
  stateId: string;
  name: string;
  tier: string;
  populationK: number;
  kind: string;
  pin: string;
  ownBranches: number;
  competitorBranches: number;
  nearestOwnKm: number | null;
  nearestCompetitorKm: number | null;
  whitespace: number;
  sub: Record<string, number>;
  overall: number;
  decision: Decision;
  dataConfidence: string;
  note: string | null;
}

export interface ScoreComponent {
  key: string;
  label: string;
  weight: number;
  score: number;
  weighted: number;
}

export interface PenaltyItem {
  label: string;
  penalty: number;
}

export interface BlendedScore {
  businessScore: number;
  mlProbability: number;
  branchIQScore: number;
  businessWeight: number;
  mlWeight: number;
  confidenceLevel: string;
  delta: number;
  decision: Decision;
  priority: string;
  note: string;
}

export interface RankedLocation {
  id: string;
  name: string;
  siteType: string;
  city: string;
  cityId: string;
  district: string;
  districtId: string;
  state: string;
  stateId: string;
  pincode: string;
  lat: number;
  lng: number;
  score: number;
  baseScore: number;
  decision: Decision;
  priority: string;
  cannibalization: Cannibalization;
  whitespaceScore: number;
  nearestOwnKm: number | null;
  nearestCompetitorKm: number | null;
  catchmentPop: number;
  mlProbability: number;
  blended: BlendedScore;
  dataConfidence: string;
  sourceType: string;
}

export interface EvidencePoint {
  text: string;
  type: string;
}

export interface NearbyBranch {
  id: string;
  bankShort: string;
  bankName: string;
  name: string;
  lat: number;
  lng: number;
  distanceKm: number;
  pincode: string;
  branchType: string;
}

export interface CatchmentRing {
  radiusKm: number;
  population: number;
  ownBranches: number;
  competitorBranches: number;
  businessDensity: number;
}

export interface Catchment {
  rings: CatchmentRing[];
  population: number;
  ownBranches: number;
  competitorBranches: number;
  nearestOwnKm: number | null;
  nearestCompetitorKm: number | null;
}

export interface MlContribution {
  feature: string;
  label: string;
  contribution: number;
  contributionPct: number;
}

export interface MlPrediction {
  probability: number;
  modelType: string;
  note: string;
  contributions: MlContribution[];
}

export interface LocationConfidence {
  level: string;
  notes: string[];
  sourceCount: number;
}

export interface LocationDetail extends RankedLocation {
  breakdown: ScoreComponent[];
  penalties: PenaltyItem[];
  totalPenalty: number;
  branchesPer10kPop: number;
  evidence: EvidencePoint[];
  catchment: Catchment;
  nearbyOwn: NearbyBranch[];
  nearbyCompetitors: NearbyBranch[];
  market: Record<string, number | string>;
  marketSource: string;
  confidence: LocationConfidence;
  mlPrediction: MlPrediction;
  disclaimer: string;
  productName: string;
}

export interface CompetitorGroup {
  bankShort: string;
  bankName: string;
  count: number;
  nearestKm: number | null;
  branches: NearbyBranch[];
}

export interface CompetitorsNear {
  center: { lat: number; lng: number };
  radiusKm: number;
  groups: CompetitorGroup[];
  total: number;
}

export interface MarketOverview {
  district: {
    id: string;
    name: string;
    state: string;
    stateId: string;
    tier: string;
    populationMn: number;
    lat: number;
    lng: number;
  };
  metrics: Record<string, number | string>;
  branchesByBank: Record<string, number>;
  branchCount: number;
  cities: City[];
  disclaimer: string;
}

export interface DataSourceEntry {
  sourceId: string;
  sourceName: string;
  organization: string;
  dataset: string;
  period: string;
  url: string;
  dataType: string;
  confidence: string;
  usedFor: string[];
}

export interface SourcesResponse {
  sources: DataSourceEntry[];
  scoringConfig: {
    location_score_weights: Record<string, number>;
    state_score_weights: Record<string, number>;
    decision_bands: { min: number; label: string; color: string }[];
    state_decision_bands: { min: number; label: string; color: string }[];
    cannibalization_bands_km: { max_km: number; risk: string; penalty: number }[];
    catchment_radii_km: number[];
  };
}

export interface QualityReport {
  branchCount: number;
  pinAreaCount: number;
  issues: Record<string, number>;
  details: { id: string; issue: string }[];
  duplicateExamples: Record<string, string>[];
  dataSource: DataSourceEntry | null;
}

export interface ConsultantAnswer {
  intent: string;
  banks: string[];
  executiveAnswer: string;
  keyEvidence: string[];
  opportunityScore: number | null;
  businessReasoning: string;
  recommendedAction: string;
  dataConfidence: string;
  supportingData: { label: string; value: string; source: string }[];
  scope: string;
}

// --- Model lab: mirrors FeatureImportance / ModelInfo / TrainingDataSummary in models/models.py ---
export interface FeatureImportance {
  feature: string;
  gain: number;
  importancePct: number;
}

export interface ModelInfo {
  status: string; // "trained" | "heuristic" | "error"
  modelType: string;
  modelVersion: string | null;
  trainedAt: string | null;
  target: string | null;
  note: string | null;
  disclaimer: string | null;
  labelDefinition: string | null;
  trainingRows: number | null;
  positiveRate: number | null;
  rowsBySourceType: Record<string, number>;
  metrics: Record<string, number>;
  featureImportances: FeatureImportance[];
  featureOrder: string[];
}

export interface TrainingDataSummary {
  rows: number;
  branches: number;
  fiscalYears: string[];
  rowsBySourceType: Record<string, number>;
  hasOfficialData: boolean;
  disclaimer: string | null;
}
