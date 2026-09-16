import React from "react";
import { useAppState } from "../store";
import {
  Sparkles,
  Award,
  AlertCircle,
  TrendingUp,
  ArrowRight,
  BookOpen,
  CheckCircle,
  HelpCircle
} from "lucide-react";

export default function AIMatcherModule() {
  const {
    matchReport,
    jobs,
    setActiveDashboardSubTab
  } = useAppState();

  const activeJob = jobs.find((j) => j.id === matchReport?.job_id) || jobs[0];

  return (
    <div id="ai-matcher-module" className="space-y-6">
      
      {/* Overview Block */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
        <div className="flex justify-between items-start border-b border-slate-850 pb-4 mb-4">
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-emerald-400">AI Compatibility Report</span>
            <h2 className="text-xl font-bold text-white mt-1">{activeJob.title}</h2>
            <span className="text-xs text-slate-400 block mt-0.5">{activeJob.company} — {activeJob.location}</span>
          </div>
          <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs px-2.5 py-1 rounded font-mono font-bold uppercase tracking-wider">
            Model: Gemini-3.5-Flash
          </span>
        </div>

        {matchReport ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            
            {/* Score Ring indicator */}
            <div className="bg-slate-950 border border-slate-850 p-6 rounded-xl flex flex-col items-center justify-center text-center">
              <div className="relative h-28 w-28 flex items-center justify-center rounded-full border-8 border-slate-900 bg-slate-950">
                <span className="text-2xl font-extrabold text-white font-mono">{matchReport.match_score}%</span>
                {/* Circular indicator simulation */}
                <svg className="absolute inset-0 h-full w-full -rotate-90">
                  <circle
                    cx="56"
                    cy="56"
                    r="48"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="8"
                    strokeDasharray="301"
                    strokeDashoffset={301 - (301 * matchReport.match_score) / 100}
                    strokeLinecap="round"
                    className="transition-all duration-1000"
                  />
                </svg>
              </div>
              <span className="text-xs font-bold text-white uppercase mt-4 tracking-wider">Overall Match Index</span>
              <span className="text-[10px] text-emerald-400 mt-1">Excellent overlap profile</span>
            </div>

            {/* Skill Gap Analysis */}
            <div className="bg-slate-950 border border-slate-850 p-6 rounded-xl space-y-4">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center">
                <AlertCircle className="h-4 w-4 text-emerald-400 mr-1" /> Skill Overlap Analysis
              </h3>

              <div className="space-y-3">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-mono mb-1">Satisfied overlaps</span>
                  <div className="flex flex-wrap gap-1">
                    {matchReport.skill_gap.matching.map((sk, idx) => (
                      <span key={idx} className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 px-2 py-0.5 rounded flex items-center">
                        <CheckCircle className="h-3 w-3 mr-1" /> {sk}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-mono mb-1">Gaps identified</span>
                  <div className="flex flex-wrap gap-1">
                    {matchReport.skill_gap.missing.map((sk, idx) => (
                      <span key={idx} className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/10 px-2 py-0.5 rounded">
                        ⚠ {sk}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Compensation audit */}
            <div className="bg-slate-950 border border-slate-850 p-6 rounded-xl flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center mb-2">
                  <TrendingUp className="h-4 w-4 text-emerald-400 mr-1" /> Market Compensation Index
                </h3>
                <span className="text-lg font-bold text-white font-mono block mt-1">{activeJob.salary_range}</span>
                <p className="text-xs text-slate-400 leading-relaxed mt-2">
                  {matchReport.salary_vs_market}
                </p>
              </div>

              <div className="text-[10px] text-slate-500 border-t border-slate-900 pt-2 font-mono">
                Source: Compiled SaaS market indexers
              </div>
            </div>

          </div>
        ) : (
          <div className="text-center py-12">
            <Sparkles className="h-10 w-10 text-slate-700 mx-auto mb-2" />
            <span className="text-xs text-slate-400 block">No calculations requested</span>
            <button
              onClick={() => setActiveDashboardSubTab("jobs")}
              className="mt-3 px-4 py-2 bg-emerald-500 text-slate-950 font-bold rounded text-xs hover:bg-emerald-400 transition-colors"
            >
              Select job and run match
            </button>
          </div>
        )}
      </div>

      {/* Recommendations & Action Plan */}
      {matchReport && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
              <Award className="h-4 w-4 text-emerald-400 mr-1" /> Custom CV Formatting Adjustments
            </h3>
            <div className="space-y-3">
              {matchReport.custom_recommendations.map((rec, i) => (
                <div key={i} className="bg-slate-950 border border-slate-850 p-4 rounded flex items-start space-x-3">
                  <span className="bg-emerald-500/10 text-emerald-400 font-mono font-bold text-xs h-6 w-6 rounded flex items-center justify-center shrink-0">
                    {i + 1}
                  </span>
                  <p className="text-xs text-slate-300 leading-normal">{rec}</p>
                </div>
              ))}
            </div>

            <button
              onClick={() => setActiveDashboardSubTab("resume")}
              className="w-full mt-4 py-2 bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded font-semibold hover:text-white hover:border-slate-700 transition-colors flex items-center justify-center space-x-1"
            >
              <span>Transfer changes directly into Resume Builder</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
              <BookOpen className="h-4 w-4 text-emerald-400 mr-1" /> Recommended Learning Roadmap
            </h3>
            <div className="space-y-3">
              <div className="bg-slate-950 border border-slate-850 p-4 rounded text-xs">
                <span className="font-bold text-white block">1. CUDA Core Kernels</span>
                <p className="text-slate-400 mt-1">Acquire foundational memory routing principles and grid execution indexes to satisfy deep ML demands.</p>
              </div>
              <div className="bg-slate-950 border border-slate-850 p-4 rounded text-xs">
                <span className="font-bold text-white block">2. High-Performance APIs</span>
                <p className="text-slate-400 mt-1">Study JAX compilation blocks and custom autograd implementations.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
