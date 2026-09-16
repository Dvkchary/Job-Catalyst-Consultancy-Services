import React, { useState } from "react";
import { useAppState } from "../store";
import {
  ShieldAlert,
  Search,
  CheckCircle,
  XCircle,
  TrendingUp,
  RotateCcw,
  Clock,
  Sparkles,
  RefreshCw
} from "lucide-react";

export default function ATSModule() {
  const {
    atsReport,
    runAtsAnalysis,
    atsHistory,
    selectedResumeVersion
  } = useAppState();

  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);

  // Initialize with some default text if available
  React.useEffect(() => {
    if (selectedResumeVersion) {
      const p = selectedResumeVersion.sections.find(s => s.type === "personal")?.content?.name || "Candidate";
      const s = selectedResumeVersion.sections.find(s => s.type === "summary")?.content || "";
      const k = (selectedResumeVersion.sections.find(s => s.type === "skills")?.content || []).join(", ");
      setResumeText(`${p}\n\nSummary:\n${s}\n\nSkills:\n${k}`);
    }
  }, [selectedResumeVersion]);

  const handleScan = (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeText || !jobDescription) return;

    setLoading(true);
    setTimeout(() => {
      runAtsAnalysis(resumeText, jobDescription);
      setLoading(false);
    }, 1500);
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return "text-emerald-400 border-emerald-500/20 bg-emerald-500/5";
    if (score >= 70) return "text-yellow-400 border-yellow-500/20 bg-yellow-500/5";
    return "text-red-400 border-red-500/20 bg-red-500/5";
  };

  return (
    <div id="ats-module" className="space-y-6">
      
      {/* Selector input parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Input box */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center">
              <Search className="h-4 w-4 text-emerald-400 mr-1" /> Document Alignment Check
            </h3>
            <span className="text-[10px] text-slate-500">Compares CV structure against job requirements</span>
          </div>

          <form onSubmit={handleScan} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Resume Copy (Plain Text)</label>
              <textarea
                rows={6}
                required
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                placeholder="Paste your resume layout content or write it here..."
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Target Job Description</label>
              <textarea
                rows={5}
                required
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                placeholder="Paste the target employer's job description listing here..."
              />
            </div>

            <button
              id="ats-scan-submit"
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-emerald-500 text-slate-950 font-bold rounded hover:bg-emerald-400 transition-colors text-xs flex items-center justify-center space-x-1.5"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Iterating Compliance Vectors...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Execute Compliance Audit Check</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results view */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          {atsReport ? (
            <div className="space-y-6">
              {/* Score card */}
              <div className="flex items-center space-x-4">
                <div className="relative flex items-center justify-center h-20 w-20 rounded-full border-4 border-slate-850 bg-slate-950">
                  <span className="text-xl font-bold font-mono text-white">{atsReport.score}%</span>
                </div>
                <div>
                  <h3 className="text-md font-bold text-white uppercase">Alignment Matching Score</h3>
                  <div className={`mt-1 text-xs border rounded px-2 py-0.5 w-fit ${getScoreColor(atsReport.score)}`}>
                    {atsReport.score >= 85 ? "Optimal compliance" : atsReport.score >= 70 ? "Moderate overlap" : "High filter risk"}
                  </div>
                </div>
              </div>

              {/* Keyword found vs missing */}
              <div className="grid grid-cols-2 gap-4 border-t border-b border-slate-800 py-4">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400 mr-1" /> Keywords Matched
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {atsReport.keywords_found.map((kw, i) => (
                      <span key={i} className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 px-2 py-0.5 rounded">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center">
                    <XCircle className="h-3.5 w-3.5 text-red-400 mr-1" /> Missing Keywords
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {atsReport.keywords_missing.map((kw, i) => (
                      <span key={i} className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/10 px-2 py-0.5 rounded">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Structual Checks */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Structural Rules Checklist</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center space-x-1.5 text-slate-350">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Contact Info found</span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-slate-350">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Executive summary parsed</span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-slate-350">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Work history present</span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-slate-350">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Core skill index found</span>
                  </div>
                </div>
              </div>

              {/* Actionable items */}
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-850">
                <h4 className="text-xs font-bold text-white mb-2 flex items-center">
                  <ShieldAlert className="h-3.5 w-3.5 text-yellow-400 mr-1" /> Actionable Improvement Hints
                </h4>
                <ul className="list-disc pl-4 text-xs text-slate-400 space-y-1">
                  {atsReport.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center py-12">
              <TrendingUp className="h-12 w-12 text-slate-700 mb-3" />
              <h3 className="text-md font-bold text-white uppercase mb-1">Waiting for inputs</h3>
              <p className="text-xs text-slate-500 max-w-xs">
                Copy-paste your CV layout alongside a target description to evaluate ATS parsing scores.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Audit History */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
          <Clock className="h-4 w-4 text-emerald-400 mr-1" /> ATS Calculation Archives
        </h3>
        <div className="space-y-2">
          {atsHistory.map((hist, i) => (
            <div key={i} className="bg-slate-950 border border-slate-850 p-3 rounded flex justify-between items-center">
              <div>
                <span className="text-xs font-semibold text-slate-200 block">{hist.title}</span>
                <span className="text-[10px] text-slate-500 mt-1 block">Scanned: {hist.timestamp}</span>
              </div>
              <span className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${hist.score >= 80 ? "bg-emerald-500/10 text-emerald-400" : "bg-yellow-500/10 text-yellow-400"}`}>
                {hist.score}% Match
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
