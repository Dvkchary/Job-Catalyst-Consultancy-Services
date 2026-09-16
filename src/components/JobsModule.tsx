import React, { useState } from "react";
import { useAppState } from "../store";
import { Job } from "../types";
import {
  Search,
  Filter,
  Bookmark,
  Briefcase,
  MapPin,
  Clock,
  ExternalLink,
  Sparkles,
  Zap,
  Building2,
  CheckCircle2
} from "lucide-react";

export default function JobsModule() {
  const {
    jobs,
    savedJobIds,
    toggleSaveJob,
    addApplication,
    runAiMatcher,
    setActiveDashboardSubTab
  } = useAppState();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [selectedJob, setSelectedJob] = useState<Job>(jobs[0]);
  const [applySuccess, setApplySuccess] = useState(false);

  // Search filter implementation
  const filteredJobs = jobs.filter((j) => {
    const query = searchQuery.toLowerCase();
    const matchQuery =
      j.title.toLowerCase().includes(query) ||
      j.company.toLowerCase().includes(query) ||
      j.skills_required.some((s) => s.toLowerCase().includes(query));
    const matchType = selectedType === "" || j.type === selectedType;
    return matchQuery && matchType;
  });

  const handleApply = (job: Job) => {
    addApplication(job.id, job.title, job.company);
    setApplySuccess(true);
    setTimeout(() => setApplySuccess(false), 3000);
  };

  const handleRunAiAudit = (job: Job) => {
    runAiMatcher(job.id);
    setActiveDashboardSubTab("matcher");
  };

  return (
    <div id="jobs-module" className="space-y-6">
      
      {/* Search and Filters Strip */}
      <div className="flex flex-col md:flex-row gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            placeholder="Search roles, companies, or specific tech competencies (e.g. PyTorch)..."
          />
        </div>

        <div className="flex space-x-2 shrink-0">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Arrangements</option>
            <option value="Full-Time">Full-Time</option>
            <option value="Remote">Remote</option>
            <option value="Hybrid">Hybrid</option>
            <option value="Contract">Contract</option>
          </select>

          <span className="bg-slate-950 border border-slate-800 text-slate-500 rounded px-2.5 py-2 text-xs flex items-center font-mono">
            Count: {filteredJobs.length}
          </span>
        </div>
      </div>

      {/* Main split: Job lists vs Job detail drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left lists panel */}
        <div className="lg:col-span-1 space-y-3 max-h-[550px] overflow-y-auto pr-1">
          {filteredJobs.length > 0 ? (
            filteredJobs.map((job) => (
              <div
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className={`w-full p-4 rounded-xl text-left border transition-all hover:border-emerald-500/30 flex flex-col justify-between cursor-pointer ${selectedJob.id === job.id ? "bg-slate-900 border-emerald-500" : "bg-slate-900/40 border-slate-850"}`}
              >
                <div>
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold text-white block truncate max-w-[150px]">{job.title}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSaveJob(job.id);
                      }}
                      className="p-1 text-slate-500 hover:text-emerald-400"
                    >
                      <Bookmark className={`h-4 w-4 ${savedJobIds.includes(job.id) ? "fill-emerald-400 text-emerald-400" : ""}`} />
                    </button>
                  </div>
                  
                  <span className="text-[11px] text-emerald-400 block font-semibold mt-0.5">{job.company}</span>
                  
                  <div className="flex items-center space-x-3 text-[10px] text-slate-400 mt-3">
                    <span className="flex items-center"><MapPin className="h-3 w-3 mr-0.5" /> {job.location}</span>
                    <span className="flex items-center"><Clock className="h-3 w-3 mr-0.5" /> {job.posted_at}</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1 mt-4">
                  {job.skills_required.slice(0, 3).map((s, idx) => (
                    <span key={idx} className="text-[9px] bg-slate-950 text-slate-400 px-1.5 py-0.5 rounded border border-slate-800">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 bg-slate-900/40 border border-slate-850 rounded-xl">
              <Briefcase className="h-8 w-8 text-slate-700 mx-auto mb-2" />
              <span className="text-xs text-slate-500 block">No roles match criteria</span>
            </div>
          )}
        </div>

        {/* Right detail specifications drawer */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between min-h-[480px]">
          {selectedJob ? (
            <div className="space-y-6">
              {/* Header profile */}
              <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                <div className="flex items-center space-x-4">
                  {selectedJob.logo ? (
                    <img src={selectedJob.logo} alt={selectedJob.company} className="h-12 w-12 rounded-lg object-cover bg-slate-950 border border-slate-800" referrerPolicy="no-referrer" />
                  ) : (
                    <div className="h-12 w-12 bg-emerald-500/10 text-emerald-400 rounded-lg flex items-center justify-center font-bold">
                      {selectedJob.company.substring(0, 2).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h3 className="text-lg font-bold text-white">{selectedJob.title}</h3>
                    <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                      <span className="flex items-center text-emerald-400 font-semibold">
                        <Building2 className="h-3.5 w-3.5 mr-1" /> {selectedJob.company}
                      </span>
                      <span>•</span>
                      <span className="flex items-center"><MapPin className="h-3 w-3 mr-1" /> {selectedJob.location}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end text-right">
                  <span className="text-sm font-bold text-white font-mono">{selectedJob.salary_range}</span>
                  <span className="text-[10px] text-slate-500 uppercase font-mono mt-1">Estimations Range</span>
                </div>
              </div>

              {/* Description */}
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Role Scope & Overview</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{selectedJob.description}</p>
              </div>

              {/* Requirements list */}
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Strict Criteria</h4>
                <ul className="list-disc pl-4 text-xs text-slate-350 space-y-1">
                  {selectedJob.requirements.map((req, i) => (
                    <li key={i}>{req}</li>
                  ))}
                </ul>
              </div>

              {/* Tech index required */}
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Technical Index Required</h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedJob.skills_required.map((s, i) => (
                    <span key={i} className="text-[10px] bg-slate-950 border border-slate-800 text-slate-300 px-2.5 py-1 rounded">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex space-x-3 pt-4 border-t border-slate-800">
                <button
                  id="jobs-ai-matcher-btn"
                  onClick={() => handleRunAiAudit(selectedJob)}
                  className="flex-1 py-2 bg-slate-950 border border-emerald-500/30 hover:border-emerald-500/55 text-emerald-400 rounded text-xs font-bold transition-all flex items-center justify-center space-x-1.5"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Execute AI Matcher Audit</span>
                </button>

                <button
                  id="jobs-apply-btn"
                  onClick={() => handleApply(selectedJob)}
                  className="px-6 py-2 bg-emerald-500 text-slate-950 rounded text-xs font-bold hover:bg-emerald-400 transition-colors flex items-center justify-center space-x-1"
                >
                  <Zap className="h-4 w-4" />
                  <span>Quick Route Apply</span>
                </button>
              </div>

              {applySuccess && (
                <p className="text-xs text-emerald-400 text-center animate-pulse flex items-center justify-center">
                  <CheckCircle2 className="h-4 w-4 mr-1" /> Successfully registered pipeline record in Applications Tracker board!
                </p>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              Select any role listed on the left to reveal specifications drawers.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
