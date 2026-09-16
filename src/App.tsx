import React, { useState } from "react";
import { AppProvider, useAppState } from "./store";
import LandingPage from "./components/LandingPage";
import AuthScreen from "./components/AuthScreen";
import DashboardOverview from "./components/DashboardOverview";
import ResumeModule from "./components/ResumeModule";
import ATSModule from "./components/ATSModule";
import JobsModule from "./components/JobsModule";
import AIMatcherModule from "./components/AIMatcherModule";
import ApplicationsTracker from "./components/ApplicationsTracker";
import InterviewModule from "./components/InterviewModule";
import CareerCoachModule from "./components/CareerCoachModule";
import BillingModule from "./components/BillingModule";
import AdminPortal from "./components/AdminPortal";
import WorkflowModule from "./components/WorkflowModule";
import {
  LayoutDashboard,
  FileSpreadsheet,
  TrendingUp,
  Briefcase,
  Sparkles,
  Layers,
  Cpu,
  Compass,
  CreditCard,
  ShieldAlert,
  Bell,
  LogOut,
  Menu,
  X,
  Mail,
  HelpCircle,
  Clock,
  UserCheck,
  Workflow
} from "lucide-react";

function MainAppContent() {
  const {
    currentTab,
    setCurrentTab,
    activeDashboardSubTab,
    setActiveDashboardSubTab,
    user,
    logout,
    notifications,
    markNotificationsAsRead,
    activePlan
  } = useAppState();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const unreadNotificationsCount = notifications.filter((n) => !n.is_read).length;

  // Sidebar Links config mapping
  const menuItems = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "resume", label: "Resume Builder", icon: FileSpreadsheet },
    { id: "ats", label: "ATS Sandbox", icon: TrendingUp },
    { id: "jobs", label: "Jobs Directory", icon: Briefcase },
    { id: "matcher", label: "AI Matcher", icon: Sparkles },
    { id: "tracker", label: "Track Pipelines", icon: Layers },
    { id: "interview", label: "Interview Coach", icon: Cpu },
    { id: "coach", label: "Career Coach", icon: Compass },
    { id: "workflows", label: "AI Workflows", icon: Workflow },
    { id: "billing", label: "Billing Hub", icon: CreditCard }
  ];

  // If the user has ADMIN roles, append Admin Portal link
  if (user?.roles.includes("ADMIN")) {
    menuItems.push({ id: "admin", label: "Admin Portal", icon: ShieldAlert });
  }

  // Active view selector
  const renderSubTab = () => {
    switch (activeDashboardSubTab) {
      case "overview":
        return <DashboardOverview />;
      case "resume":
        return <ResumeModule />;
      case "ats":
        return <ATSModule />;
      case "jobs":
        return <JobsModule />;
      case "matcher":
        return <AIMatcherModule />;
      case "tracker":
        return <ApplicationsTracker />;
      case "interview":
        return <InterviewModule />;
      case "coach":
        return <CareerCoachModule />;
      case "workflows":
        return <WorkflowModule />;
      case "billing":
        return <BillingModule />;
      case "admin":
        return <AdminPortal />;
      default:
        return <DashboardOverview />;
    }
  };

  // 1. Landing Screen Route
  if (currentTab === "landing") {
    return <LandingPage />;
  }

  // 2. Authentication Route
  if (currentTab === "auth") {
    return <AuthScreen />;
  }

  // 3. Authenticated SaaS Core Dashboard Route
  return (
    <div id="main-saas-dashboard" className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* Upper Navigation Header bar */}
      <header className="sticky top-0 z-40 bg-slate-900 border-b border-slate-800 h-16 flex items-center justify-between px-4 sm:px-6">
        <div className="flex items-center space-x-3">
          {/* Mobile navigation slider toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 text-slate-400 hover:text-white"
          >
            <Menu className="h-5 w-5" />
          </button>
          
          <div className="flex items-center space-x-2">
            <div className="bg-emerald-500 text-slate-950 p-1.5 rounded font-mono font-bold tracking-tighter text-md">
              JC
            </div>
            <span className="font-bold tracking-tight text-white hidden sm:inline">
              JobCatalyst <span className="text-emerald-400">AI</span>
            </span>
          </div>
        </div>

        {/* Profile elements and notification bell */}
        <div className="flex items-center space-x-4">
          
          {/* Unread Alert badge */}
          <div className="relative">
            <button
              onClick={() => {
                setNotificationsOpen(!notificationsOpen);
                markNotificationsAsRead();
              }}
              className="p-1.5 text-slate-450 hover:text-white relative bg-slate-950/40 rounded border border-slate-850"
            >
              <Bell className="h-4.5 w-4.5" />
              {unreadNotificationsCount > 0 && (
                <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              )}
            </button>

            {/* Notifications Dropdown Panel */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-3 w-80 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-2xl z-50">
                <div className="flex justify-between items-center border-b border-slate-850 pb-2.5 mb-2.5">
                  <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center">
                    <Bell className="h-4 w-4 text-emerald-400 mr-1" /> Dynamic System Alerts
                  </span>
                  <button onClick={() => setNotificationsOpen(false)} className="text-slate-500 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="space-y-2.5 max-h-60 overflow-y-auto">
                  {notifications.map((item) => (
                    <div key={item.id} className="bg-slate-950 border border-slate-850 p-2.5 rounded text-xs leading-normal">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-bold text-slate-200">{item.title}</span>
                        <span className="text-[9px] text-slate-500 font-mono">{item.timestamp}</span>
                      </div>
                      <p className="text-slate-400">{item.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* User badge */}
          <div className="hidden md:flex flex-col items-end text-right">
            <span className="text-xs font-bold text-slate-100 font-sans">{user?.username}</span>
            <span className="text-[9px] uppercase tracking-wider text-emerald-400 font-bold">
              {activePlan.name}
            </span>
          </div>

          <button
            onClick={logout}
            className="p-1.5 text-slate-450 hover:text-white bg-slate-950/40 rounded border border-slate-850 flex items-center space-x-1"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </header>

      {/* Main Workspace Frame */}
      <div className="flex flex-1 relative">
        
        {/* Sidebar Frame */}
        <aside className="hidden md:block w-64 bg-slate-900 border-r border-slate-800 p-5 flex flex-col justify-between shrink-0">
          <div className="space-y-1.5">
            <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 block mb-3 pl-2">
              SaaS Navigation Suite
            </span>
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeDashboardSubTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveDashboardSubTab(item.id as any)}
                    className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded text-xs font-bold transition-all text-left ${isActive ? "bg-emerald-500 text-slate-950 font-extrabold shadow-md shadow-emerald-500/10" : "text-slate-400 hover:text-slate-200 hover:bg-slate-950"}`}
                  >
                    <Icon className="h-4.5 w-4.5 shrink-0" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="text-[10px] text-slate-600 font-mono border-t border-slate-850 pt-4 mt-auto">
            <span>Client Platform: v1.0.0-rc1</span>
          </div>
        </aside>

        {/* Responsive Mobile Drawer Navigation Menu */}
        {mobileMenuOpen && (
          <div className="absolute inset-0 z-50 bg-slate-950/90 backdrop-blur-sm md:hidden flex justify-start">
            <div className="w-64 bg-slate-900 h-full p-5 flex flex-col justify-between border-r border-slate-800">
              <div>
                <div className="flex justify-between items-center pb-4 border-b border-slate-850 mb-4">
                  <span className="text-xs font-extrabold text-white uppercase tracking-wider">Navigation Menu</span>
                  <button onClick={() => setMobileMenuOpen(false)} className="text-slate-400 hover:text-white">
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <nav className="space-y-1.5">
                  {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeDashboardSubTab === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          setActiveDashboardSubTab(item.id as any);
                          setMobileMenuOpen(false);
                        }}
                        className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded text-xs font-bold transition-all text-left ${isActive ? "bg-emerald-500 text-slate-950 font-extrabold" : "text-slate-450 hover:text-white hover:bg-slate-950"}`}
                      >
                        <Icon className="h-4.5 w-4.5" />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              <div className="border-t border-slate-850 pt-3">
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-xs font-bold text-red-400 hover:bg-red-950/20 rounded transition-colors"
                >
                  <LogOut className="h-4.5 w-4.5" />
                  <span>Logout Profile</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Viewport Content Block */}
        <main className="flex-1 p-6 sm:p-8 max-w-7xl mx-auto overflow-y-auto">
          {renderSubTab()}
        </main>
      </div>

    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <MainAppContent />
    </AppProvider>
  );
}
