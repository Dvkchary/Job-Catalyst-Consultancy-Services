import React, { useState } from "react";
import { useAppState } from "../store";
import {
  Sparkles,
  TrendingUp,
  MapPin,
  Compass,
  Award,
  BookOpen,
  ArrowRight,
  Calculator
} from "lucide-react";

export default function CareerCoachModule() {
  const [selectedTrack, setSelectedTrack] = useState<"ai_research" | "fullstack">("ai_research");
  const [userSalary, setUserSalary] = useState("120000");
  const [calculatedDiff, setCalculatedDiff] = useState<number | null>(null);

  const tracks = {
    ai_research: {
      title: "AI Research Specialist Roadmap",
      milestones: [
        { title: "Deep Mathematical Frameworks", desc: "Gain thorough competency in matrix routing, backpropagation gradients, and loss landscape optimization vectors." },
        { title: "Transformer Alignment & RLHF", desc: "Acquire hands-on mastery in standard alignment protocols, DPO, and expert scoring architectures." },
        { title: "Distributed Compute Training", desc: "Explore deep sharding algorithms, CUDA memory layout alignments, and scaling JAX pipelines across server clusters." }
      ],
      courses: [
        { title: "Distributed Training Mechanics", provider: "Stanford Online", duration: "12 weeks" },
        { title: "Generative Model Autopilots", provider: "DeepMind Academy", duration: "6 weeks" }
      ],
      marketAvg: 195000
    },
    fullstack: {
      title: "Principal SaaS Product Developer",
      milestones: [
        { title: "Enterprise Systems Design", desc: "Master load-balancers, DB connection caching engines, and state replication." },
        { title: "SaaS Billing Ledger Protocols", desc: "Learn transactional safety matrices, dynamic proration ledgers, and secure proxy integrations." },
        { title: "Interactive UI/UX Orchestration", desc: "Perfect responsive custom layouts, fluid transitions, and accessible state caching." }
      ],
      courses: [
        { title: "Advanced System Designs", provider: "MIT Professional", duration: "8 weeks" },
        { title: "SaaS Payment Flow Masterclass", provider: "Stripe Developer", duration: "4 weeks" }
      ],
      marketAvg: 165000
    }
  };

  const handleSalarySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const currentTrack = tracks[selectedTrack];
    const diff = currentTrack.marketAvg - Number(userSalary);
    setCalculatedDiff(diff);
  };

  return (
    <div id="career-coach-module" className="space-y-6 font-sans">
      
      {/* Tab selection */}
      <div className="flex space-x-3 border-b border-slate-800 pb-3">
        <button
          onClick={() => {
            setSelectedTrack("ai_research");
            setCalculatedDiff(null);
          }}
          className={`px-4 py-2 text-xs font-bold rounded transition-all ${selectedTrack === "ai_research" ? "bg-emerald-500 text-slate-950 shadow" : "text-slate-450 hover:text-white"}`}
        >
          AI Research Track
        </button>
        <button
          onClick={() => {
            setSelectedTrack("fullstack");
            setCalculatedDiff(null);
          }}
          className={`px-4 py-2 text-xs font-bold rounded transition-all ${selectedTrack === "fullstack" ? "bg-emerald-500 text-slate-950 shadow" : "text-slate-450 hover:text-white"}`}
        >
          Principal Full-Stack Track
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Milestones sequences */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center mb-6">
            <Compass className="h-4 w-4 text-emerald-400 mr-1" /> Roadmaps & Milestone Targets
          </h3>

          <div className="space-y-6">
            {tracks[selectedTrack].milestones.map((ms, idx) => (
              <div key={idx} className="relative pl-8 border-l-2 border-slate-800 pb-1">
                <div className="absolute -left-[11px] top-0 h-5 w-5 rounded-full bg-emerald-500 border-4 border-slate-900 flex items-center justify-center font-bold text-[9px] text-slate-950">
                  {idx + 1}
                </div>
                <h4 className="text-sm font-bold text-slate-100">{ms.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed mt-1.5">{ms.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Salary insights calculator */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
              <Calculator className="h-4 w-4 text-emerald-400 mr-1" /> Regional Salary Estimations
            </h3>

            <form onSubmit={handleSalarySubmit} className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Your Current Salary (USD)</label>
                <input
                  type="number"
                  required
                  value={userSalary}
                  onChange={(e) => setUserSalary(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  placeholder="e.g. 120000"
                />
              </div>

              <button type="submit" className="w-full py-1.5 bg-emerald-500 text-slate-950 rounded text-xs font-bold hover:bg-emerald-400 transition-colors">
                Contrast Against Market Average
              </button>
            </form>

            {calculatedDiff !== null && (
              <div className="mt-6 bg-slate-950 p-4 rounded border border-slate-850 text-xs">
                <span className="text-slate-500 uppercase block font-mono">Market Gap Contrast</span>
                {calculatedDiff > 0 ? (
                  <p className="mt-1 text-slate-255 leading-relaxed">
                    You are currently earning <span className="text-emerald-400 font-bold font-mono">${calculatedDiff.toLocaleString()}</span> below the market average of <span className="font-bold text-white font-mono">${tracks[selectedTrack].marketAvg.toLocaleString()}</span> for this specialty.
                  </p>
                ) : (
                  <p className="mt-1 text-slate-255 leading-relaxed">
                    Splendid! Your package stands <span className="text-emerald-400 font-bold font-mono">${Math.abs(calculatedDiff).toLocaleString()}</span> above the average market benchmark!
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="border-t border-slate-850 pt-3 mt-6">
            <span className="text-[10px] text-slate-500 font-mono uppercase block mb-2">Targeted Catalog Courses</span>
            <div className="space-y-2">
              {tracks[selectedTrack].courses.map((c, i) => (
                <div key={i} className="bg-slate-950 p-2.5 rounded border border-slate-850 flex justify-between items-center text-xs">
                  <div>
                    <span className="font-bold text-slate-200 block">{c.title}</span>
                    <span className="text-[9px] text-slate-500 mt-0.5 block">{c.provider}</span>
                  </div>
                  <span className="text-[9px] font-mono text-slate-400 whitespace-nowrap">{c.duration}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
