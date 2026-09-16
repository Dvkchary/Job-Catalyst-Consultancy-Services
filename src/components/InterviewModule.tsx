import React, { useState } from "react";
import { useAppState } from "../store";
import {
  Cpu,
  Mic,
  MessageSquare,
  Play,
  CheckCircle,
  HelpCircle,
  TrendingUp,
  RotateCcw,
  RefreshCw,
  Send
} from "lucide-react";

export default function InterviewModule() {
  const {
    interviews,
    activeInterview,
    startMockInterview,
    sendInterviewMessage,
    completeInterview
  } = useAppState();

  // Setup form state
  const [jobTitle, setJobTitle] = useState("Lead AI Research Engineer");
  const [company, setCompany] = useState("Google DeepMind");
  const [mode, setMode] = useState<"text" | "audio">("text");
  const [inputMsg, setInputMsg] = useState("");

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    if (jobTitle && company) {
      startMockInterview(jobTitle, company, mode);
    }
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMsg.trim()) {
      sendInterviewMessage(inputMsg.trim());
      setInputMsg("");
    }
  };

  return (
    <div id="interview-platform-module" className="space-y-6 font-sans">
      
      {/* Session setup OR active chat board */}
      {!activeInterview ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Setup Panel */}
          <div className="lg:col-span-1 bg-slate-900 border border-slate-800 p-6 rounded-xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
              <Cpu className="h-4 w-4 text-emerald-400 mr-1" /> Mock Session Setup
            </h3>

            <form onSubmit={handleStart} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Target Role Title</label>
                <input
                  type="text"
                  required
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  placeholder="e.g. Senior Full-Stack Developer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Target Employer Company</label>
                <input
                  type="text"
                  required
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  placeholder="e.g. Google DeepMind"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Coach Interaction Mode</label>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <button
                    type="button"
                    onClick={() => setMode("text")}
                    className={`p-3 rounded border text-center transition-all ${mode === "text" ? "border-emerald-500 bg-emerald-500/10 text-white" : "border-slate-850 bg-slate-950 text-slate-400"}`}
                  >
                    <MessageSquare className="h-4 w-4 mx-auto mb-1" />
                    <span className="text-[10px] font-bold block">Text Messaging</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setMode("audio")}
                    className={`p-3 rounded border text-center transition-all ${mode === "audio" ? "border-emerald-500 bg-emerald-500/10 text-white" : "border-slate-850 bg-slate-950 text-slate-400"}`}
                  >
                    <Mic className="h-4 w-4 mx-auto mb-1" />
                    <span className="text-[10px] font-bold block">Speech Simulator</span>
                  </button>
                </div>
              </div>

              <button
                id="start-interview-btn"
                type="submit"
                className="w-full py-2 bg-emerald-500 text-slate-950 rounded text-xs font-bold hover:bg-emerald-400 transition-colors flex items-center justify-center space-x-1"
              >
                <Play className="h-3.5 w-3.5" />
                <span>Initialize AI Session</span>
              </button>
            </form>
          </div>

          {/* Past Evaluations list */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center border-b border-slate-850 pb-2">
              <TrendingUp className="h-4 w-4 text-emerald-400 mr-1" /> Historical Session Ratings
            </h3>

            <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
              {interviews.map((session) => (
                <div key={session.id} className="bg-slate-950 border border-slate-850 p-4 rounded-lg space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-bold text-white block">{session.job_title}</span>
                      <span className="text-[10px] text-emerald-400 block font-semibold">{session.company}</span>
                    </div>
                    {session.score && (
                      <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                        Score: {session.score}%
                      </span>
                    )}
                  </div>

                  {session.feedback && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 border-t border-slate-900 pt-3 text-[11px]">
                      <div>
                        <span className="text-slate-500 block uppercase">Clarity Score</span>
                        <span className="font-bold text-slate-200">{session.feedback.clarity}/10</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase">Relevance Index</span>
                        <span className="font-bold text-slate-200">{session.feedback.relevance}/10</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase">Depth Overlap</span>
                        <span className="font-bold text-slate-200">{session.feedback.depth}/10</span>
                      </div>
                    </div>
                  )}

                  {session.feedback && (
                    <p className="text-[11px] text-slate-400 border-t border-slate-900 pt-2 italic leading-relaxed">
                      Coach Remarks: "{session.feedback.general_remarks}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

        </div>
      ) : (
        /* Active Chat Workspace */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Conversational Screen */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col h-[500px] justify-between">
            <div className="flex justify-between items-center border-b border-slate-850 pb-3 mb-3">
              <div>
                <span className="text-[10px] uppercase font-bold text-emerald-400">Live AI Interview Session</span>
                <h3 className="text-xs font-bold text-white">{activeInterview.job_title}</h3>
              </div>

              <button
                id="complete-interview-btn"
                onClick={completeInterview}
                className="px-3 py-1 bg-emerald-500 text-slate-950 font-bold rounded text-[10px] uppercase hover:bg-emerald-400 transition-colors"
              >
                Complete & Compile Feedback
              </button>
            </div>

            {/* Chat list */}
            <div className="flex-1 overflow-y-auto space-y-3.5 pr-1 py-2">
              {activeInterview.transcript.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.sender === "candidate" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] rounded-xl p-3.5 text-xs leading-relaxed ${msg.sender === "candidate" ? "bg-emerald-500 text-slate-950 rounded-tr-none font-medium" : "bg-slate-950 border border-slate-850 text-slate-300 rounded-tl-none"}`}>
                    <span className="text-[9px] uppercase block mb-1 opacity-70 tracking-wider">
                      {msg.sender === "candidate" ? "You" : "AI Coach"}
                    </span>
                    <p>{msg.text}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Message inputs form */}
            <form onSubmit={handleSend} className="flex space-x-2 pt-3 border-t border-slate-850">
              <input
                type="text"
                required
                value={inputMsg}
                onChange={(e) => setInputMsg(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none"
                placeholder={activeInterview.mode === "audio" ? "Simulate speech response or type message..." : "Type response answers..."}
              />
              <button type="submit" className="bg-emerald-500 text-slate-950 p-2 rounded hover:bg-emerald-400 transition-colors shrink-0">
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>

          {/* Coach side hints widget */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex flex-col justify-between">
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-white uppercase tracking-widest flex items-center">
                <Mic className="h-4 w-4 text-emerald-400 mr-1" /> Active speech checklist
              </h4>

              <div className="space-y-3 text-xs text-slate-400">
                <div className="bg-slate-950 p-3.5 rounded border border-slate-850">
                  <span className="font-bold text-white block">STAR Structural rule</span>
                  <p className="mt-1 leading-normal text-[11px]">Begin by setting the Situation, highlight task constraints, detail your technical Action, and present output Results.</p>
                </div>

                <div className="bg-slate-950 p-3.5 rounded border border-slate-850">
                  <span className="font-bold text-white block">Keyword overlap index</span>
                  <p className="mt-1 leading-normal text-[11px]">Be sure to mention key competencies such as PyTorch, memory optimization or activation checkpointing when suitable.</p>
                </div>
              </div>
            </div>

            <div className="text-[10px] text-slate-500 text-center font-mono border-t border-slate-850 pt-3">
              Latency: 1.4s • Streaming codec enabled
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
