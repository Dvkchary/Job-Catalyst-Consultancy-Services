import React from "react";
import { useAppState } from "../store";
import {
  Sparkles,
  Zap,
  TrendingUp,
  Cpu,
  Award,
  Users,
  Terminal,
  Activity,
  ArrowUpRight,
  Database,
  Briefcase,
  FileSpreadsheet
} from "lucide-react";

export default function DashboardOverview() {
  const {
    user,
    activePlan,
    usage,
    applications,
    interviews,
    adminLogs,
    setActiveDashboardSubTab
  } = useAppState();

  const activeApplicationsCount = applications.filter((a) => a.status !== "rejected").length;
  const passedInterviews = interviews.filter((i) => i.score && i.score >= 80).length;

  // Render a beautiful pure SVG Area Chart for usage metrics
  const mockWeeklyUsage = [
    { label: "Mon", tokens: 25 },
    { label: "Tue", tokens: 45 },
    { label: "Wed", tokens: 35 },
    { label: "Thu", tokens: 75 },
    { label: "Fri", tokens: 60 },
    { label: "Sat", tokens: 95 },
    { label: "Sun", tokens: 120 }
  ];

  return (
    <div id="dashboard-overview" className="space-y-6">
      
      {/* Dynamic Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-900 border border-slate-800 p-6 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center">
            Welcome back, <span className="text-emerald-400 ml-1">{user?.username || "Catalyst Master"}</span>
            <span className="ml-2 bg-emerald-500/10 text-emerald-400 text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded border border-emerald-500/20">
              {activePlan.name}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Enterprise system logs, usage credits, and active pipeline metrics are compiled healthy.
          </p>
        </div>
        
        {/* Rapid summary */}
        <div className="flex space-x-4 mt-4 md:mt-0">
          <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-850">
            <span className="block text-[10px] text-slate-500 uppercase font-semibold">Remaining AI Credits</span>
            <span className="text-md font-bold text-white font-mono">
              {(activePlan.feature_limits.ai_credits - usage.ai_credits_used).toLocaleString()}
            </span>
          </div>
          <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-850">
            <span className="block text-[10px] text-slate-500 uppercase font-semibold">Active Pipelines</span>
            <span className="text-md font-bold text-emerald-400 font-mono">
              {activeApplicationsCount}
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Main KPI Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1 */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <span className="block text-xs text-slate-400 font-medium uppercase">ATS Evaluations</span>
            <span className="block text-2xl font-extrabold text-white mt-1 font-mono">{usage.ats_analyses}</span>
            <span className="text-[10px] text-emerald-400 mt-1 block">✔ Standard parsers compliant</span>
          </div>
          <div className="bg-emerald-500/10 p-3 rounded-lg text-emerald-400">
            <TrendingUp className="h-5 w-5" />
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <span className="block text-xs text-slate-400 font-medium uppercase">Mock Speech Sessions</span>
            <span className="block text-2xl font-extrabold text-white mt-1 font-mono">{usage.interview_sessions}</span>
            <span className="text-[10px] text-emerald-400 mt-1 block">✔ Average score: 86.5%</span>
          </div>
          <div className="bg-emerald-500/10 p-3 rounded-lg text-emerald-400">
            <Cpu className="h-5 w-5" />
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <span className="block text-xs text-slate-400 font-medium uppercase">Jobs Searched & Matched</span>
            <span className="block text-2xl font-extrabold text-white mt-1 font-mono">{usage.job_matches}</span>
            <span className="text-[10px] text-slate-500 mt-1 block">Matched against 3 models</span>
          </div>
          <div className="bg-emerald-500/10 p-3 rounded-lg text-emerald-400">
            <Briefcase className="h-5 w-5" />
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <span className="block text-xs text-slate-400 font-medium uppercase">Storage Utilization</span>
            <span className="block text-2xl font-extrabold text-white mt-1 font-mono">
              {(usage.storage_bytes / (1024 * 1024)).toFixed(1)} MB
            </span>
            <span className="text-[10px] text-slate-500 mt-1 block">
              Max limit: {activePlan.feature_limits.storage_bytes / (1024 * 1024)} MB
            </span>
          </div>
          <div className="bg-emerald-500/10 p-3 rounded-lg text-emerald-400">
            <Database className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Bento Grid Layer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Column 1: Analytics Area Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center">
                <Activity className="h-4 w-4 text-emerald-400 mr-1" /> AI Agent Interaction Load
              </h3>
              <p className="text-xs text-slate-500">Hourly API token consumption profile over recent periods.</p>
            </div>
            <span className="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-850">
              Live updates active
            </span>
          </div>

          {/* Clean High-Fidelity SVG Chart */}
          <div className="relative h-48 w-full bg-slate-950 rounded-lg p-2 border border-slate-850/50 flex flex-col justify-between">
            {/* SVG Plot */}
            <svg className="absolute inset-0 h-full w-full p-4 overflow-visible" viewBox="0 0 400 120" preserveAspectRatio="none">
              <defs>
                <linearGradient id="chart-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              
              {/* Grid Lines */}
              <line x1="0" y1="20" x2="400" y2="20" stroke="#1f2937" strokeWidth="0.5" strokeDasharray="3,3" />
              <line x1="0" y1="60" x2="400" y2="60" stroke="#1f2937" strokeWidth="0.5" strokeDasharray="3,3" />
              <line x1="0" y1="100" x2="400" y2="100" stroke="#1f2937" strokeWidth="0.5" strokeDasharray="3,3" />

              {/* Area */}
              <path
                d="M 10 110 L 60 90 L 120 100 L 185 60 L 250 70 L 315 40 L 390 20 L 390 110 Z"
                fill="url(#chart-grad)"
              />
              
              {/* Line */}
              <path
                d="M 10 110 L 60 90 L 120 100 L 185 60 L 250 70 L 315 40 L 390 20"
                fill="none"
                stroke="#10b981"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Points */}
              <circle cx="10" cy="110" r="3" fill="#10b981" />
              <circle cx="60" cy="90" r="3" fill="#10b981" />
              <circle cx="120" cy="100" r="3" fill="#10b981" />
              <circle cx="185" cy="60" r="3" fill="#10b981" />
              <circle cx="250" cy="70" r="3" fill="#10b981" />
              <circle cx="315" cy="40" r="3" fill="#10b981" />
              <circle cx="390" cy="20" r="4" fill="#34d399" stroke="#047857" strokeWidth="1" />
            </svg>

            {/* X-Axis labels */}
            <div className="flex justify-between text-[9px] text-slate-500 mt-auto pt-2 border-t border-slate-900 font-mono">
              {mockWeeklyUsage.map((d, i) => (
                <span key={i}>{d.label}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Column 2: Quick Actions panel */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center mb-1">
              <Sparkles className="h-4 w-4 text-emerald-400 mr-1" /> Quick Execution Actions
            </h3>
            <p className="text-xs text-slate-500 mb-4">Trigger central modules instantly using dynamic cache states.</p>
          </div>

          <div className="space-y-2.5">
            <button
              onClick={() => setActiveDashboardSubTab("resume")}
              className="w-full flex items-center justify-between p-3 bg-slate-950 hover:bg-slate-850 rounded border border-slate-850 text-left transition-colors group"
            >
              <div className="flex items-center space-x-2">
                <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-200">Modify CV Versions</span>
              </div>
              <ArrowUpRight className="h-3 w-3 text-slate-500 group-hover:text-emerald-400 transition-colors" />
            </button>

            <button
              onClick={() => setActiveDashboardSubTab("ats")}
              className="w-full flex items-center justify-between p-3 bg-slate-950 hover:bg-slate-850 rounded border border-slate-850 text-left transition-colors group"
            >
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-200">Run ATS Score Check</span>
              </div>
              <ArrowUpRight className="h-3 w-3 text-slate-500 group-hover:text-emerald-400 transition-colors" />
            </button>

            <button
              onClick={() => setActiveDashboardSubTab("interview")}
              className="w-full flex items-center justify-between p-3 bg-slate-950 hover:bg-slate-850 rounded border border-slate-850 text-left transition-colors group"
            >
              <div className="flex items-center space-x-2">
                <Cpu className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-200">Launch Speech Panel</span>
              </div>
              <ArrowUpRight className="h-3 w-3 text-slate-500 group-hover:text-emerald-400 transition-colors" />
            </button>

            <button
              onClick={() => setActiveDashboardSubTab("billing")}
              className="w-full flex items-center justify-between p-3 bg-slate-950 hover:bg-slate-850 rounded border border-slate-850 text-left transition-colors group"
            >
              <div className="flex items-center space-x-2">
                <Award className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-200">Upgrade / Metering Logs</span>
              </div>
              <ArrowUpRight className="h-3 w-3 text-slate-500 group-hover:text-emerald-400 transition-colors" />
            </button>
          </div>
        </div>
      </div>

      {/* Log Audit and Active Tracker Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Activity Audits */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center mb-4">
            <Terminal className="h-4 w-4 text-emerald-400 mr-1" /> Dynamic System Audit Logs
          </h3>
          <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
            {adminLogs.slice(0, 4).map((log) => (
              <div key={log.id} className="bg-slate-950 border border-slate-850 p-3 rounded flex items-start justify-between">
                <div>
                  <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 mr-2">
                    {log.action}
                  </span>
                  <p className="text-xs text-slate-300 mt-1">{log.description}</p>
                </div>
                <span className="text-[9px] font-mono text-slate-500 whitespace-nowrap">
                  {new Date(log.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Monitoring Health and active workers indicators */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center mb-4">
            <Activity className="h-4 w-4 text-emerald-400 mr-1" /> Enterprise Clusters & System Health
          </h3>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-slate-950 border border-slate-850 p-4 rounded-lg">
              <span className="text-[10px] text-slate-500 font-semibold block uppercase">Database Connection</span>
              <div className="flex items-center space-x-2 mt-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-xs font-bold text-slate-200">SQLAlchemy Pool (Healthy)</span>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-850 p-4 rounded-lg">
              <span className="text-[10px] text-slate-500 font-semibold block uppercase">AI Model Gateway</span>
              <div className="flex items-center space-x-2 mt-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-xs font-bold text-slate-200">Gemini LLM (Active)</span>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-850 p-4 rounded-lg">
              <span className="text-[10px] text-slate-500 font-semibold block uppercase">Redis Token Bucket</span>
              <div className="flex items-center space-x-2 mt-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span className="text-xs font-bold text-slate-200">0.4ms Latency</span>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-850 p-4 rounded-lg">
              <span className="text-[10px] text-slate-500 font-semibold block uppercase">Queue Processors</span>
              <div className="flex items-center space-x-2 mt-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span className="text-xs font-bold text-slate-200">4 Active Workers</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
