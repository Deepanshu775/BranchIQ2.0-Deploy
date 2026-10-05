import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Brain, Database, Play, RefreshCw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiPost } from "@/lib/api";
import { useModelInfo, useTrainingData } from "@/lib/branchiq";

const PCT = (v: number | null | undefined) => (v == null ? "—" : `${Math.round(v * 100)}%`);

export default function ModelLab() {
  const { data: info, isLoading: infoLoading } = useModelInfo();
  const { data: panel } = useTrainingData();
  const qc = useQueryClient();
  const [token, setToken] = useState("");

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["model-info"] });
    void qc.invalidateQueries({ queryKey: ["model-training-data"] });
  };

  const panelMutation = useMutation({
    mutationFn: () => apiPost<{ rows: number }>("/model/generate-panel", { adminToken: token, replace: true }),
    onSuccess: (r) => {
      toast.success(`Training panel rebuilt — ${r.rows.toLocaleString()} rows`);
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message || "Panel generation failed"),
  });

  const trainMutation = useMutation({
    mutationFn: () => apiPost<{ metrics: Record<string, number> }>("/model/train", { adminToken: token }),
    onSuccess: (r) => {
      toast.success(`Model trained — holdout ROC-AUC ${r.metrics?.rocAuc ?? "n/a"}`);
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message || "Training failed"),
  });

  const trained = info?.status === "trained";
  const busy = panelMutation.isPending || trainMutation.isPending;

  return (
    <div className="space-y-5" data-testid="model-lab-page">
      <div className="accent-line">
        <div className="eyebrow">BranchIQ 2.0 · Prediction layer</div>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-[#0B1220]">Model &amp; Training</h1>
        <p className="mt-1 max-w-3xl text-sm text-slate-600">
          BranchIQ trains an XGBoost classifier on ingested branch-performance history and blends its
          probability with the transparent business score. Until history exists, the heuristic model serves
          predictions — the API contract is identical either way.
        </p>
      </div>

      {/* Status strip */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="bq-card bq-shadow p-5" data-testid="model-status-card">
          <div className="flex items-center gap-2">
            <Brain size={16} className="text-[#1687F8]" />
            <span className="eyebrow">Active predictor</span>
          </div>
          <div
            className={`mt-2 inline-flex rounded-md px-2 py-1 text-xs font-bold uppercase tracking-wide ${
              trained ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
            }`}
            data-testid="model-status-badge"
          >
            {infoLoading ? "loading" : trained ? "XGBoost — trained" : "Heuristic fallback"}
          </div>
          <p className="mt-2 text-sm font-medium text-[#0F172A]" data-testid="model-type">
            {info?.modelType || "—"}
          </p>
          {info?.trainedAt && (
            <p className="mt-1 text-xs text-slate-600" data-testid="model-trained-at">
              Trained {new Date(info.trainedAt).toLocaleString()}
            </p>
          )}
          <p className="mt-2 text-xs text-slate-600" data-testid="model-note">
            {info?.note || info?.target || ""}
          </p>
        </div>

        <div className="bq-card bq-shadow p-5" data-testid="model-metrics-card">
          <span className="eyebrow">Holdout metrics</span>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <Metric label="ROC-AUC" value={info?.metrics?.rocAuc ?? null} testid="metric-roc-auc" />
            <Metric label="Accuracy" value={info?.metrics?.accuracy ?? null} testid="metric-accuracy" />
            <Metric label="Train rows" value={info?.metrics?.trainRows ?? null} testid="metric-train-rows" />
            <Metric label="Test rows" value={info?.metrics?.testRows ?? null} testid="metric-test-rows" />
          </div>
          <p className="mt-3 text-xs text-slate-600" data-testid="model-label-definition">
            {info?.labelDefinition ? `Label: ${info.labelDefinition}.` : "No trained artifact yet."}
            {info?.positiveRate != null && ` Positive class share ${PCT(info.positiveRate)}.`}
          </p>
        </div>

        <div className="bq-card bq-shadow p-5" data-testid="training-data-card">
          <div className="flex items-center gap-2">
            <Database size={16} className="text-[#1687F8]" />
            <span className="eyebrow">Training data</span>
          </div>
          <p className="stat-num mt-2 text-2xl text-[#0B1220]" data-testid="training-rows">
            {(panel?.rows ?? 0).toLocaleString()}
          </p>
          <p className="text-xs text-slate-600" data-testid="training-branches">
            performance rows · {(panel?.branches ?? 0).toLocaleString()} branches ·{" "}
            {panel?.fiscalYears?.length ?? 0} fiscal years
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {Object.entries(panel?.rowsBySourceType ?? {}).map(([k, v]) => (
              <span
                key={k}
                className="rounded-md border border-[#DFE7F0] bg-white px-2 py-0.5 text-[11px] font-semibold text-slate-700"
                data-testid={`source-type-${k}`}
              >
                {k}: {v.toLocaleString()}
              </span>
            ))}
          </div>
          <p className="mt-2 text-xs text-slate-600" data-testid="training-official-flag">
            {panel?.hasOfficialData
              ? "Real ingested history present — training prefers it."
              : "No official history ingested yet."}
          </p>
        </div>
      </div>

      {/* Feature importance */}
      <div className="bq-card bq-shadow p-5" data-testid="feature-importance-card">
        <div className="flex items-center justify-between">
          <div>
            <span className="eyebrow">Explainability · §20</span>
            <h2 className="font-display text-lg font-semibold text-[#0B1220]">Feature importance (gain)</h2>
          </div>
          <span className="rounded-md bg-[#071426] px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-white">
            Model prediction
          </span>
        </div>
        {trained && (info?.featureImportances?.length ?? 0) > 0 ? (
          <div className="mt-4 space-y-2">
            {info!.featureImportances.map((f) => (
              <div key={f.feature} className="flex items-center gap-3" data-testid={`importance-${f.feature}`}>
                <span className="w-56 shrink-0 text-sm text-slate-700">{f.feature}</span>
                <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-[#EEF2F8]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[#1687F8] to-[#27C3E8] transition-[width] duration-500"
                    style={{ width: `${Math.max(2, f.importancePct)}%` }}
                  />
                </div>
                <span className="stat-num w-14 text-right text-sm text-[#0B1220]">{f.importancePct}%</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-600" data-testid="feature-importance-empty">
            Feature importance appears once the XGBoost model has been trained. The heuristic model
            publishes its per-feature contributions on each location detail instead.
          </p>
        )}
      </div>

      {/* Controls */}
      <div className="bq-card bq-shadow p-5" data-testid="training-controls">
        <span className="eyebrow">Run training</span>
        <p className="mt-1 text-sm text-slate-600">
          Training is admin-gated. Supply the server&apos;s admin token, then rebuild the panel and fit the
          model. The same pipeline runs headless via{" "}
          <code className="rounded bg-[#F1F5F9] px-1 py-0.5 text-[12px]">python train_model.py --panel</code>.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Input
            data-testid="admin-token-input"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Admin token"
            className="h-9 w-[220px] border-[#DFE7F0] bg-white text-sm"
          />
          <Button
            variant="outline"
            className="h-9"
            data-testid="btn-generate-panel"
            disabled={!token || busy}
            onClick={() => panelMutation.mutate()}
          >
            <RefreshCw size={14} className={panelMutation.isPending ? "animate-spin" : ""} />
            Rebuild demo panel
          </Button>
          <Button
            className="h-9"
            data-testid="btn-train-model"
            disabled={!token || busy}
            onClick={() => trainMutation.mutate()}
          >
            <Play size={14} />
            Train XGBoost
          </Button>
        </div>
      </div>

      <div
        className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-sm text-amber-900"
        data-testid="model-disclaimer"
      >
        <AlertTriangle size={16} className="mt-0.5 shrink-0" />
        <span>
          {info?.disclaimer ||
            "MODEL PREDICTION — the performance history currently loaded is the clearly labelled DEMO/TRAINING panel. Metrics describe that demo data only and are not real-world validation. Ingest a real historical dataset (CSV) to train on official data."}
        </span>
      </div>
    </div>
  );
}

function Metric({ label, value, testid }: { label: string; value: number | null; testid: string }) {
  return (
    <div>
      <div className="eyebrow">{label}</div>
      <div className="stat-num text-xl text-[#0B1220]" data-testid={testid}>
        {value == null ? "—" : value}
      </div>
    </div>
  );
}
