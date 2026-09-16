import React, { useState } from "react";
import { useAppState } from "../store";
import {
  Users,
  Shield,
  Sliders,
  Terminal,
  Activity,
  UserCheck,
  Search,
  CheckCircle,
  ToggleLeft,
  ToggleRight,
  Settings,
  Cpu
} from "lucide-react";

export default function AdminPortal() {
  const {
    adminUsers,
    adminConfigs,
    adminFlags,
    adminLogs,
    updateAdminUserStatus,
    updateAdminUserRoles,
    updateSystemConfig,
    updateFeatureFlag
  } = useAppState();

  const [activeTab, setActiveTab] = useState<"users" | "configs" | "flags" | "logs">("users");
  const [userSearch, setUserSearch] = useState("");
  const [logSearch, setLogSearch] = useState("");

  const filteredUsers = adminUsers.filter(u =>
    u.username.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.email.toLowerCase().includes(userSearch.toLowerCase())
  );

  const filteredLogs = adminLogs.filter(log =>
    log.description.toLowerCase().includes(logSearch.toLowerCase()) ||
    log.action.toLowerCase().includes(logSearch.toLowerCase())
  );

  return (
    <div id="admin-portal" className="space-y-6 font-sans">
      
      {/* Top Navigation Toggles */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-900 border border-slate-800 p-4 rounded-xl gap-3">
        <div>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center">
            <Shield className="h-4 w-4 text-emerald-400 mr-1" /> Enterprise Systems Administration
          </h2>
          <p className="text-xs text-slate-400">Manage directory identities, adjust SLA settings, and track logs.</p>
        </div>

        <div className="flex space-x-2">
          {["users", "configs", "flags", "logs"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-3 py-1.5 text-xs font-bold rounded transition-all capitalize ${activeTab === tab ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white bg-slate-950 border border-slate-850"}`}
            >
              {tab === "configs" ? "SLA Settings" : tab === "flags" ? "Rollout Flags" : tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab views */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 min-h-[420px]">
        
        {/* VIEW 1: Accounts */}
        {activeTab === "users" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-850">
              <h3 className="text-sm font-bold text-white uppercase">Directory Identities & RBAC Claims</h3>
              <div className="relative w-64">
                <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded pl-8 pr-2.5 py-1 text-xs text-white focus:outline-none"
                  placeholder="Search email, username..."
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-350">
                <thead className="bg-slate-950 border-b border-slate-850 font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">Account profile</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Roles / RBAC Claims</th>
                    <th className="px-4 py-3 text-right">Administrative Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {filteredUsers.map((usr) => (
                    <tr key={usr.id} className="hover:bg-slate-950/40">
                      <td className="px-4 py-3">
                        <span className="font-semibold text-white block">{usr.username}</span>
                        <span className="text-[10px] text-slate-500 mt-0.5 block">{usr.email}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded ${usr.status === "ACTIVE" ? "bg-emerald-500/10 text-emerald-400" : usr.status === "PENDING" ? "bg-yellow-500/10 text-yellow-400" : "bg-red-500/10 text-red-400"}`}>
                          {usr.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-[10px] text-slate-200">
                        {usr.roles.join(", ")}
                      </td>
                      <td className="px-4 py-3 text-right space-x-1.5">
                        <button
                          onClick={() => updateAdminUserStatus(usr.id, usr.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE")}
                          className="px-2 py-1 bg-slate-950 border border-slate-850 hover:border-slate-750 text-slate-400 text-[10px] rounded transition-colors"
                        >
                          Toggle Lock status
                        </button>
                        <button
                          onClick={() => updateAdminUserRoles(usr.id, usr.roles.includes("ADMIN") ? ["USER"] : ["ADMIN", "USER"])}
                          className="px-2 py-1 bg-slate-950 border border-slate-850 hover:border-slate-750 text-slate-400 text-[10px] rounded transition-colors"
                        >
                          Modify Claims
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* VIEW 2: Configurations */}
        {activeTab === "configs" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase border-b border-slate-850 pb-3 mb-4">
              SLA Variable Configs & AI Proxies
            </h3>

            <div className="space-y-4 max-w-2xl">
              {adminConfigs.map((cfg) => (
                <div key={cfg.id} className="bg-slate-950 border border-slate-850 p-4 rounded-lg space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-200 text-xs font-mono">{cfg.config_key}</span>
                    <span className="text-[9px] uppercase tracking-wider text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                      {cfg.category}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">{cfg.description}</p>
                  
                  <div className="flex space-x-2 pt-2">
                    <input
                      type="text"
                      defaultValue={cfg.config_value}
                      onBlur={(e) => updateSystemConfig(cfg.config_key, e.target.value)}
                      className="flex-1 bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-xs text-white font-mono"
                    />
                    <span className="text-[10px] text-slate-500 bg-slate-900 border border-slate-800 px-2 py-1 rounded flex items-center shrink-0">
                      Auto-saved on blur
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VIEW 3: Feature Flags */}
        {activeTab === "flags" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase border-b border-slate-850 pb-3 mb-4">
              Rollouts & progressive toggles
            </h3>

            <div className="space-y-4 max-w-2xl">
              {adminFlags.map((flag) => (
                <div key={flag.id} className="bg-slate-950 border border-slate-850 p-4 rounded-lg flex items-center justify-between">
                  <div className="space-y-1 pr-4">
                    <span className="font-bold text-slate-100 text-xs font-mono flex items-center">
                      {flag.name}
                      <span className="ml-2 bg-slate-900 text-slate-400 text-[9px] font-mono border border-slate-800 px-1.5 py-0.2 rounded">
                        Rollout: {flag.rollout_percentage}%
                      </span>
                    </span>
                    <p className="text-[11px] text-slate-400 leading-normal">{flag.description}</p>
                  </div>

                  <button
                    onClick={() => updateFeatureFlag(flag.id, { is_enabled: !flag.is_enabled })}
                    className="text-emerald-400 hover:text-emerald-300 shrink-0"
                  >
                    {flag.is_enabled ? (
                      <ToggleRight className="h-9 w-9 text-emerald-400" />
                    ) : (
                      <ToggleLeft className="h-9 w-9 text-slate-600" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VIEW 4: Searchable Audit Logs */}
        {activeTab === "logs" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-850">
              <h3 className="text-sm font-bold text-white uppercase">SaaS Audit Chronicle</h3>
              <div className="relative w-64">
                <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  value={logSearch}
                  onChange={(e) => setLogSearch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded pl-8 pr-2.5 py-1 text-xs text-white focus:outline-none"
                  placeholder="Filter logs by keyword..."
                />
              </div>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {filteredLogs.map((log) => (
                <div key={log.id} className="bg-slate-950 border border-slate-850 p-3 rounded flex items-start justify-between text-xs">
                  <div>
                    <span className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 bg-slate-900 border border-slate-800 rounded text-slate-400 mr-2">
                      {log.action}
                    </span>
                    <span className="text-slate-500 font-mono text-[10px]">User: {log.username}</span>
                    <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">{log.description}</p>
                  </div>

                  <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap ml-4">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
              ))}

              {filteredLogs.length === 0 && (
                <div className="text-center py-12 text-xs text-slate-500">
                  No audit trail records found matching search queries.
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
