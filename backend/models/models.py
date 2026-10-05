"""Pydantic v2 models — every response model here has a hand-written TS mirror in
frontend/src/types/api.ts. Keep the pair in sync in the same edit (typed-fetch boundary).
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class Bank(BaseModel):
    id: str
    short: str
    name: str
    sector: str
    reportingPeriod: str
    branches: int
    deposits: float
    advances: float
    depositGrowth: float
    creditGrowth: float
    digitalReadiness: int
    geographicCoverage: int
    footprintWeight: float
    source: str
    sourceUrl: str


class State(BaseModel):
    id: str
    name: str
    region: str
    lat: float
    lng: float
    populationMn: float
    indicators: Dict[str, Any]


class District(BaseModel):
    id: str
    stateId: str
    state: str
    name: str
    lat: float
    lng: float
    populationMn: float
    tier: str


class City(BaseModel):
    id: str
    stateId: str
    districtId: str
    name: str
    lat: float
    lng: float
    populationK: float
    pin: str
    kind: str
    tier: str


class Pincode(BaseModel):
    id: str
    pin: str
    cityId: str
    districtId: str
    stateId: str
    localityName: str
    lat: float
    lng: float
    catchmentPopK: float
    pinSource: str


class Branch(BaseModel):
    id: str
    bankId: str
    bankShort: str
    bankName: str
    name: str
    code: str
    stateId: str
    districtId: str
    cityId: str
    city: str
    pincode: str
    lat: float
    lng: float
    branchType: str
    openingDate: str
    sourceType: str
    status: str
    lastVerified: str


class BranchPage(BaseModel):
    total: int
    items: List[Branch]


class Decision(BaseModel):
    label: str
    color: str


class Cannibalization(BaseModel):
    risk: str
    penalty: float
    nearestOwnKm: Optional[float] = None
    note: str


class Driver(BaseModel):
    key: str
    label: str
    value: int


class StateRanked(BaseModel):
    id: str
    state: str
    region: str
    populationMn: float
    score: int
    sub: Dict[str, int]
    presence: int
    decision: Decision
    priority: str
    drivers: List[Driver]
    recommendation: str
    dataConfidence: str


class DistrictRanked(BaseModel):
    id: str
    stateId: str
    state: str
    name: str
    tier: str
    populationMn: float
    ownBranches: int
    totalBranches: int
    competitorBranches: int
    penetrationPct: float
    sub: Dict[str, int]
    overall: int
    decision: Decision
    priority: str
    drivers: List[Driver]
    dataConfidence: str


class CityRanked(BaseModel):
    id: str
    districtId: str
    district: str
    stateId: str
    name: str
    tier: str
    populationK: float
    kind: str
    pin: str
    ownBranches: int
    competitorBranches: int
    nearestOwnKm: Optional[float] = None
    nearestCompetitorKm: Optional[float] = None
    whitespace: int
    sub: Dict[str, int]
    overall: int
    decision: Decision
    dataConfidence: str
    note: Optional[str] = None


class ScoreComponent(BaseModel):
    key: str
    label: str
    weight: float
    score: int
    weighted: float


class PenaltyItem(BaseModel):
    label: str
    penalty: float


class RankedLocation(BaseModel):
    id: str
    name: str
    siteType: str
    city: str
    cityId: str
    district: str
    districtId: str
    state: str
    stateId: str
    pincode: str
    lat: float
    lng: float
    score: int
    baseScore: int
    decision: Decision
    priority: str
    cannibalization: Cannibalization
    whitespaceScore: int
    nearestOwnKm: Optional[float] = None
    nearestCompetitorKm: Optional[float] = None
    catchmentPop: int
    mlProbability: float
    blended: "BlendedScore"
    dataConfidence: str
    sourceType: str


class BlendedScore(BaseModel):
    businessScore: int
    mlProbability: float
    branchIQScore: int
    businessWeight: float
    mlWeight: float
    confidenceLevel: str
    delta: int
    decision: Decision
    priority: str
    note: str


class EvidencePoint(BaseModel):
    text: str
    type: str


class NearbyBranch(BaseModel):
    id: str
    bankShort: str
    bankName: str
    name: str
    lat: float
    lng: float
    distanceKm: float
    pincode: str
    branchType: str


class CatchmentRing(BaseModel):
    radiusKm: float
    population: int
    ownBranches: int
    competitorBranches: int
    businessDensity: int


class Catchment(BaseModel):
    rings: List[CatchmentRing]
    population: int
    ownBranches: int
    competitorBranches: int
    nearestOwnKm: Optional[float] = None
    nearestCompetitorKm: Optional[float] = None


class MlPrediction(BaseModel):
    probability: float
    modelType: str
    note: str
    contributions: List[Dict[str, Any]]


class FeatureImportance(BaseModel):
    feature: str
    gain: float
    importancePct: float


class ModelInfo(BaseModel):
    status: str                       # "trained" | "heuristic" | "error"
    modelType: str
    modelVersion: Optional[str] = None
    trainedAt: Optional[str] = None
    target: Optional[str] = None
    note: Optional[str] = None
    disclaimer: Optional[str] = None
    labelDefinition: Optional[str] = None
    trainingRows: Optional[int] = None
    positiveRate: Optional[float] = None
    rowsBySourceType: Dict[str, int] = {}
    metrics: Dict[str, float] = {}
    featureImportances: List[FeatureImportance] = []
    featureOrder: List[str] = []


class TrainingDataSummary(BaseModel):
    rows: int
    branches: int
    fiscalYears: List[str]
    rowsBySourceType: Dict[str, int]
    hasOfficialData: bool
    disclaimer: Optional[str] = None


class TrainRequest(BaseModel):
    adminToken: str


class TrainPanelRequest(BaseModel):
    adminToken: str
    replace: bool = True


class LocationConfidence(BaseModel):
    level: str
    notes: List[str]
    sourceCount: int


class LocationDetail(RankedLocation):
    breakdown: List[ScoreComponent]
    penalties: List[PenaltyItem]
    totalPenalty: float
    branchesPer10kPop: float
    evidence: List[EvidencePoint]
    catchment: Catchment
    nearbyOwn: List[NearbyBranch]
    nearbyCompetitors: List[NearbyBranch]
    market: Dict[str, Any]
    marketSource: str
    confidence: LocationConfidence
    mlPrediction: MlPrediction
    disclaimer: str
    productName: str


class CompetitorGroup(BaseModel):
    bankShort: str
    bankName: str
    count: int
    nearestKm: Optional[float] = None
    branches: List[NearbyBranch]


class CompetitorsNear(BaseModel):
    center: Dict[str, float]
    radiusKm: float
    groups: List[CompetitorGroup]
    total: int


class QualityReport(BaseModel):
    branchCount: int
    pinAreaCount: int
    issues: Dict[str, int]
    details: List[Dict[str, str]]
    duplicateExamples: List[Dict[str, Any]]
    dataSource: Optional[Dict[str, Any]] = None


# ------------------------------------------------------- consultant
class ConsultantRequest(BaseModel):
    question: str
    selectedBank: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class ConsultantResponse(BaseModel):
    intent: str
    banks: List[str] = Field(default_factory=list)
    executiveAnswer: str
    keyEvidence: List[str] = Field(default_factory=list)
    opportunityScore: Optional[int] = None
    businessReasoning: str
    recommendedAction: str
    dataConfidence: str = "MEDIUM"
    supportingData: List[Dict[str, Any]] = Field(default_factory=list)
    scope: str = "STATE"
