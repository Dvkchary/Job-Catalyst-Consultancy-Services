import React, { useState } from "react";
import { useAppState } from "../store";
import { Application } from "../types";
import {
  FileText,
  Calendar,
  Layers,
  ArrowRight,
  UserCheck,
  Plus,
  StickyNote,
  Clock,
  Briefcase
} from "lucide-react";

export default function ApplicationsTracker() {
  const {
    applications,
    moveApplicationStatus,
    addRecruiterNote
  } = useAppState();

  const [selectedApp, setSelectedApp] = useState<Application | null>(applications[0] || null);
  const [newNote, setNewNote] = useState("");

  const columns = [
    { id: "applied", label: "Applied", color: "border-slate-800 bg-slate-900/10 text-slate-400" },
    { id: "screening", label: "Screening", color: "border-yellow-500/20 bg-yellow-500/5 text-yellow-400" },
    { id: "interviewing", label: "Interviewing", color: "border-emerald-500/20 bg-emerald-500/5 text-emerald-400" },
    { id: "offered", label: "Offered", color: "border-teal-500/20 bg-teal-500/5 text-teal-400" },
    { id: "rejected", label: "Archived", color: "border-red-500/20 bg-red-500/5 text-red-400" }
  ];

  const handleNoteSubmit = (e: React.FormEvent, appId: string) => {
    e.preventDefault();
    if (newNote.trim()) {
      addRecruiterNote(appId, newNote.trim());
      setNewNote("");
    }
  };

  return (
    <div id="applications-tracker" className="space-y-6 font-sans">
      
      {/* Board Pipeline Columns */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {columns.map((col) => {
          const colApps = applications.filter((app) => app.status === col.id);
          return (
            <div key={col.id} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-800">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">{col.label}</span>
                  <span className="text-[10px] bg-slate-950 px-2 py-0.5 rounded text-slate-400 font-mono">
                    {colApps.length}
                  </span>
                </div>

                <div className="space-y-2">
                  {colApps.map((app) => (
                    <button
                      key={app.id}
                      onClick={() => setSelectedApp(app)}
                      className={`w-full p-3 rounded text-left border bg-slate-950 transition-all ${selectedApp?.id === app.id ? "border-emerald-500 shadow-md shadow-emerald-500/5" : "border-slate-850 hover:border-slate-750"}`}
                    >
                      <span className="text-xs font-bold text-white block truncate">{app.job_title}</span>
                      <span className="text-[10px] text-emerald-400 block mt-0.5 font-semibold">{app.company}</span>
                      <span className="text-[9px] text-slate-500 block mt-2 font-mono">Applied: {app.applied_date}</span>
                    </button>
                  ))}
                </div>
              </div>

              {colApps.length === 0 && (
                <div className="text-center py-6 text-[10px] text-slate-500 font-mono">
                  Empty column
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Detail Split Section */}
      {selectedApp ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 bg-slate-900 border border-slate-800 rounded-xl p-6">
          
          {/* Main Info Box */}
          <div className="lg:col-span-1 space-y-4">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400">Selected Pipeline Detail</span>
              <h3 className="text-lg font-bold text-white mt-1">{selectedApp.job_title}</h3>
              <span className="text-xs text-slate-400 block mt-0.5">{selectedApp.company}</span>
            </div>

            {/* Quick transition action */}
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-850 space-y-2.5">
              <span className="text-[10px] text-slate-500 font-mono uppercase block">Adjust Status Parameter</span>
              <div className="grid grid-cols-2 gap-1.5">
                {columns.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => {
                      moveApplicationStatus(selectedApp.id, c.id as any);
                      // Update the local selection view with the updated application
                      setSelectedApp({
                        ...selectedApp,
                        status: c.id as any,
                        timeline: [
                          ...selectedApp.timeline,
                          { title: `Moved to ${c.label}`, date: "Today" }
                        ]
                      });
                    }}
                    className={`px-2 py-1 text-[10px] font-semibold rounded text-center transition-colors ${selectedApp.status === c.id ? "bg-emerald-500 text-slate-950" : "bg-slate-900 text-slate-450 hover:bg-slate-850"}`}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Recruiter Details */}
            <div className="space-y-2">
              <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 block">Recruiter Contact Details</span>
              {selectedApp.recruiters.length > 0 ? (
                selectedApp.recruiters.map((rec, i) => (
                  <div key={i} className="bg-slate-950 p-3 rounded border border-slate-850 text-xs">
                    <span className="font-bold text-slate-200 block">{rec.name}</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">{rec.contact || "No contact logged"}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 italic bg-slate-950 p-3 rounded border border-slate-850">
                  No personnel logged. Add details inside standard profiles.
                </div>
              )}
            </div>
          </div>

          {/* Timeline Milestones list */}
          <div className="lg:col-span-1 space-y-4 border-t lg:border-t-0 lg:border-l lg:border-r border-slate-800 px-0 lg:px-6">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center">
              <Clock className="h-4 w-4 text-emerald-400 mr-1" /> Historic Application Milestones
            </h4>
            <div className="space-y-4">
              {selectedApp.timeline.map((item, idx) => (
                <div key={idx} className="relative pl-5 border-l border-slate-800 text-xs">
                  <div className="absolute -left-1.5 top-1.5 h-3 w-3 rounded-full bg-emerald-500 border-2 border-slate-950" />
                  <div className="flex justify-between items-start">
                    <span className="font-bold text-slate-200">{item.title}</span>
                    <span className="text-[9px] font-mono text-slate-500">{item.date}</span>
                  </div>
                  {item.description && <p className="text-slate-450 text-[11px] mt-0.5 leading-normal">{item.description}</p>}
                </div>
              ))}
            </div>
          </div>

          {/* Note Box inputs */}
          <div className="lg:col-span-1 space-y-4">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center">
              <StickyNote className="h-4 w-4 text-emerald-400 mr-1" /> Dynamic Application Notes
            </h4>
            
            <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
              {selectedApp.notes.map((note, idx) => (
                <div key={idx} className="bg-slate-950 p-3 rounded text-xs text-slate-350 border border-slate-850 leading-relaxed">
                  {note}
                </div>
              ))}
              {selectedApp.notes.length === 0 && (
                <span className="text-xs text-slate-500 italic">No panel notes added. Fill input below to add logs.</span>
              )}
            </div>

            <form onSubmit={(e) => handleNoteSubmit(e, selectedApp.id)} className="space-y-2 pt-2">
              <textarea
                rows={2}
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
                placeholder="Type achievements, callback dates or phone notes..."
              />
              <button type="submit" className="w-full py-1.5 bg-emerald-500 text-slate-950 rounded text-xs font-bold hover:bg-emerald-400 transition-colors">
                Append Panel Note
              </button>
            </form>
          </div>

        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-xs">
          Select any active application pipeline tile to review tracking timeline maps and documents.
        </div>
      )}
    </div>
  );
}
