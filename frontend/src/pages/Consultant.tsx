import { useState } from "react";
import { ChevronDown, Compass, Loader2, Send, Sparkles } from "lucide-react";

import { ConfidenceBadge, DataBadge, DecisionBadge, SectionTitle } from "@/components/shared/Ui";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useApp } from "@/context/AppContext";
import { apiPost } from "@/lib/api";
import type { ConsultantAnswer } from "@/types/api";

const EXAMPLES = [
  "Where should this bank expand in Uttar Pradesh?",
  "Which districts have the highest whitespace?",
  "Give me the top 10 branch locations in this market.",
  "Why is this district attractive?",
  "What are the risks of opening a branch here?",
  "Should the bank open a physical branch or go digital-first?",
];

export default function Consultant() {
  const { selectedBank, stateId, districtId, cityId, locationId } = useApp();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<ConsultantAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showData, setShowData] = useState(false);

  const ask = async (q?: string) => {
    const question = (q ?? query).trim();
    if (!question || loading) return;
    setQuery(question);
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      // The backend does intent detection + data retrieval from the analytics engine; the LLM
      // only explains those structured results, so it cannot invent banking statistics.
      const data = await apiPost<ConsultantAnswer>("/consultant/ask", {
        question,
        selectedBank,
        context: { stateId, districtId, cityId, locationId },
      });
      setAnswer(data);
    } catch {
      setError("BranchIQ could not complete the analysis. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="page-consultant">
      <SectionTitle
        eyebrow="AI Consulting Team"
        title="Ask BranchIQ"
        subtitle="Strategic questions. Data-backed answers grounded on BranchIQ's analytical engine."
        testid="section-consultant"
      />

      <div className="bq-card bq-shadow p-4" data-testid="consultant-scope">
        <div className="eyebrow mb-2">Active analysis scope (sent to the engine)</div>
        <div className="flex flex-wrap gap-1.5 text-xs">
          <span className="rounded-md bg-[#071426] px-2 py-1 font-semibold text-white">{selectedBank}</span>
          {[
            ["State", stateId],
            ["District", districtId],
            ["City", cityId],
            ["Location", locationId],
          ]
            .filter(([, v]) => !!v)
            .map(([label, v]) => (
              <span key={label as string} className="rounded-md border border-[#DFE7F0] bg-white px-2 py-1 text-slate-700">
                {label}: <span className="font-mono text-[10px]">{String(v).split("::").pop()}</span>
              </span>
            ))}
          {!stateId && (
            <span className="text-slate-400">
              Drill down in Location Intelligence first for location-specific answers.
            </span>
          )}
        </div>
      </div>

      <div className="bq-card bq-shadow p-5">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles size={16} className="text-[#1687F8]" />
          <span className="text-sm font-semibold text-[#071426]">Strategic Query</span>
        </div>
        <Textarea
          data-testid="consultant-query-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask();
          }}
          placeholder="Ask a branch expansion strategy question..."
          className="min-h-[90px] resize-none border-[#DFE7F0] text-sm"
        />
        <div className="mt-3 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">Press ⌘/Ctrl + Enter to submit</span>
          <Button
            data-testid="btn-ask-consultant"
            onClick={() => ask()}
            disabled={loading || !query.trim()}
            className="gap-2 bg-[#071426] text-white hover:bg-[#0C1D33]"
          >
            {loading ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
            {loading ? "Analyzing..." : "Ask BranchIQ"}
          </Button>
        </div>
        <div className="mt-4">
          <div className="eyebrow mb-2">Example Questions</div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                data-testid={`example-${ex.slice(0, 12).replace(/[^a-zA-Z]+/g, "-").toLowerCase()}`}
                onClick={() => ask(ex)}
                disabled={loading}
                className="rounded-full border border-[#DFE7F0] bg-white px-3 py-1.5 text-xs text-slate-600 transition-colors hover:border-[#1687F8] hover:text-[#1687F8] disabled:opacity-50"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && (
        <div className="bq-card bq-shadow p-6 text-center" data-testid="consultant-loading">
          <Loader2 size={26} className="mx-auto mb-3 animate-spin text-[#1687F8]" />
          <div className="text-sm font-medium text-[#071426]">Retrieving BranchIQ analytics and synthesising…</div>
        </div>
      )}

      {error && !loading && (
        <div className="bq-card border-rose-200 bg-rose-50 p-4 text-sm text-rose-700" data-testid="consultant-error">
          {error}
        </div>
      )}

      {answer && !loading && (
        <div className="bq-card bq-shadow bq-fade overflow-hidden" data-testid="consultant-response">
          <div className="flex flex-wrap items-center gap-2 bg-[#071426] px-5 py-3 text-white">
            <Compass size={16} className="text-cyan-300" />
            <span className="font-display font-bold">BranchIQ Strategic Assessment</span>
            <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] font-semibold">{answer.intent}</span>
            <span className="rounded bg-cyan-400/20 px-2 py-0.5 text-[10px] font-semibold text-cyan-200">
              SCOPE: {answer.scope}
            </span>
            <span className="ml-auto">
              <ConfidenceBadge level={answer.dataConfidence} />
            </span>
          </div>
          <div className="space-y-5 p-5">
            <div data-testid="response-executive-answer">
              <div className="eyebrow mb-1.5">Executive Answer</div>
              <p className="text-base font-medium leading-relaxed text-[#071426]">{answer.executiveAnswer}</p>
            </div>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_200px]">
              <div data-testid="response-evidence">
                <div className="eyebrow mb-1.5">Key Evidence</div>
                <ul className="space-y-1.5">
                  {answer.keyEvidence.map((e, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1687F8]" />
                      {e}
                    </li>
                  ))}
                </ul>
              </div>
              {answer.opportunityScore !== null && (
                <div className="flex flex-col items-center justify-center rounded-lg bg-[#F4F7FB] p-4 text-center" data-testid="response-score">
                  <div className="eyebrow mb-1">Opportunity Score</div>
                  <div className="font-display text-4xl font-bold text-[#071426]">{answer.opportunityScore}</div>
                  <div className="mb-2 text-xs text-slate-400">/ 100</div>
                  <DecisionBadge
                    decision={{
                      label: answer.opportunityScore >= 80 ? "HIGH PRIORITY" : answer.opportunityScore >= 65 ? "SELECTIVE" : "MONITOR",
                      color: answer.opportunityScore >= 80 ? "#16A36A" : answer.opportunityScore >= 65 ? "#1687F8" : "#E79B24",
                    }}
                  />
                </div>
              )}
            </div>

            <div data-testid="response-reasoning">
              <div className="eyebrow mb-1.5">Business Reasoning</div>
              <p className="text-sm leading-relaxed text-slate-700">{answer.businessReasoning}</p>
            </div>

            <div className="rounded-lg border border-[#1687F8]/30 bg-blue-50/50 p-4" data-testid="response-action">
              <div className="eyebrow mb-1.5 text-[#1687F8]">Recommended Action</div>
              <p className="text-sm font-medium leading-relaxed text-[#071426]">{answer.recommendedAction}</p>
            </div>

            {answer.supportingData.length > 0 && (
              <div>
                <button
                  data-testid="view-supporting-data"
                  onClick={() => setShowData((v) => !v)}
                  className="flex items-center gap-1.5 text-sm font-semibold text-[#1687F8] hover:underline"
                >
                  <ChevronDown size={15} /> View supporting data
                </button>
                {showData && (
                  <div className="mt-3 overflow-hidden rounded-lg border border-[#DFE7F0]">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-[#F4F7FB] text-left text-[11px] uppercase tracking-wide text-slate-500">
                          <th className="px-3 py-2">Indicator</th>
                          <th className="px-3 py-2">Value</th>
                          <th className="px-3 py-2">Source / Type</th>
                        </tr>
                      </thead>
                      <tbody>
                        {answer.supportingData.map((d, i) => (
                          <tr key={i} className="border-t border-[#EEF2F8]">
                            <td className="px-3 py-2 text-slate-700">{d.label}</td>
                            <td className="px-3 py-2 font-mono text-[#0C1D33]">{d.value}</td>
                            <td className="px-3 py-2 text-xs text-slate-500">{d.source}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center gap-2 pt-1">
              <DataBadge type="analytical" />
              <span className="text-[11px] text-slate-400">
                Model-generated strategic assessment — not an official bank recommendation.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
