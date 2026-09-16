import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Play,
  Settings,
  Plus,
  Trash2,
  Workflow as WorkflowIcon,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileCode,
  Layers,
  ChevronRight,
  Clock,
  ArrowRight,
  Sparkles,
  Info,
  Sliders,
  Send,
  PlusCircle,
  FolderSync,
  CornerDownRight,
  Terminal,
  RotateCw,
  Search,
  BookOpen
} from "lucide-react";
import { Workflow, WorkflowExecution, WorkflowTemplate, WorkflowLog } from "../types";

export default function WorkflowModule() {
  const [activeTab, setActiveTab] = useState<"workflows" | "templates" | "history">("workflows");
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [history, setHistory] = useState<WorkflowExecution[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Builder Modal / Creation States
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<Partial<Workflow> | null>(null);
  
  // Selection / Monitoring States
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [executionLogs, setExecutionLogs] = useState<WorkflowLog[]>([]);
  const [isRefreshingLogs, setIsRefreshingLogs] = useState(false);

  // Status Alerts
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  const showToast = (message: string, type: "success" | "error" | "info" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // ==============================================================================
  // Simulation Data Seeding for Client Demonstration and Fallback
  // ==============================================================================
  useEffect(() => {
    // Seed templates
    const seedTemplates: WorkflowTemplate[] = [
      {
        id: "tpl-resume-opt",
        name: "Automated Resume Refinement & Keywords injector",
        description: "Triggered instantly on resume upload. Parses the target job description to match skills gaps, uses Gemini Flash to rewrite segments with STAR impact metrics, and verifies formatting constraints.",
        category: "Resume Optimization",
        trigger_type: "EVENT_DRIVEN",
        trigger_config: { event: "resume.uploaded" },
        definition: {
          steps: [
            {
              id: "step_1",
              name: "Extract Target Job Keywords",
              type: "action",
              action_type: "call_ai",
              config: { prompt: "Analyze the uploaded target job description for critical keywords and technical skills." }
            },
            {
              id: "step_2",
              name: "Calculate ATS Match score",
              type: "action",
              action_type: "call_internal_api",
              config: { endpoint: "/api/v1/ats/evaluate", method: "POST" }
            },
            {
              id: "step_3",
              name: "Perform STAR impact rewriting",
              type: "action",
              action_type: "call_ai",
              config: { prompt: "Rewrite work bullet-points with matching action-oriented verbs using metrics: {{context.resume_text}}" }
            },
            {
              id: "step_4",
              name: "Notify User",
              type: "action",
              action_type: "create_notification",
              config: { title: "ATS Match optimized!", message: "Your revised resume is ready with an improved keyword density matching score of 87%." }
            }
          ]
        },
        is_system: true
      },
      {
        id: "tpl-job-matcher",
        name: "Enterprise Daily Matcher & Scraper scheduler",
        description: "Runs automatically on a cron schedule. Automatically pulls fresh matching listings, evaluates compatibility index, and drafts highly tailored cover letters for matching roles.",
        category: "Job Matching",
        trigger_type: "SCHEDULED",
        trigger_config: { cron: "0 9 * * *" },
        definition: {
          steps: [
            {
              id: "step_1",
              name: "Scrape Target Listings",
              type: "action",
              action_type: "call_internal_api",
              config: { endpoint: "/api/v1/jobs/recommendations", method: "GET" }
            },
            {
              id: "step_2",
              name: "Filter compatibility index",
              type: "condition",
              condition_type: "if",
              config: { expression: "{{steps_state.step_1.output.jobs_count}} > 0" },
              true_steps: [
                {
                  id: "step_3",
                  name: "Draft tailored cover letters",
                  type: "action",
                  action_type: "call_ai",
                  config: { prompt: "Write an impact cover letter matching my skills: {{context.skills}} to the recommended jobs." }
                }
              ]
            }
          ]
        },
        is_system: true
      },
      {
        id: "tpl-approval-pipeline",
        name: "Interactive Auto-Application Submission Gate",
        description: "An advanced automated pipeline that matches, drafts materials, but halts at a user approval step before auto-submitting.",
        category: "Application Submission",
        trigger_type: "MANUAL",
        trigger_config: {},
        definition: {
          steps: [
            {
              id: "step_1",
              name: "Generate Application Packet",
              type: "action",
              action_type: "generate_report",
              config: { report_type: "SubmissionPacket" }
            },
            {
              id: "step_2",
              name: "Await Candidate Final Approval",
              type: "condition",
              condition_type: "approval",
              config: { message: "Review and click approve to transmit this application directly." }
            },
            {
              id: "step_3",
              name: "Transmit to Job Board",
              type: "action",
              action_type: "run_background_job",
              config: { job_name: "AutoTransmitSubmit" }
            }
          ]
        },
        is_system: true
      }
    ];

    const seedWorkflows: Workflow[] = [
      {
        id: "wf-1",
        user_id: "user-1",
        name: "ATS Compliance Refinement Engine",
        description: "Instantly optimizes skills matching density when uploading draft resumes.",
        trigger_type: "EVENT_DRIVEN",
        trigger_config: { event: "resume.uploaded" },
        definition: seedTemplates[0].definition,
        is_active: true,
        status: "ACTIVE",
        last_run_at: "2026-07-02T10:15:00Z",
        created_at: "2026-06-30T09:00:00Z",
        updated_at: "2026-07-02T10:15:00Z"
      },
      {
        id: "wf-2",
        user_id: "user-1",
        name: "Daily Smart Career Matcher & Scraper",
        description: "Checks local boards daily, ranks postings by suitability index and alerts me via push notification.",
        trigger_type: "SCHEDULED",
        trigger_config: { cron: "0 9 * * *" },
        definition: seedTemplates[1].definition,
        is_active: true,
        status: "ACTIVE",
        last_run_at: "2026-07-02T09:00:00Z",
        created_at: "2026-07-01T12:00:00Z",
        updated_at: "2026-07-02T09:00:00Z"
      }
    ];

    const seedHistory: WorkflowExecution[] = [
      {
        id: "exec-1",
        workflow_id: "wf-1",
        workflow: seedWorkflows[0],
        user_id: "user-1",
        status: "COMPLETED",
        trigger_source: "EVENT",
        current_step_index: 3,
        context_data: { resume_text: "Lead Software Architect at AcmeCorp" },
        steps_state: {
          step_1: { status: "COMPLETED", output: { keywords: ["react", "node", "typescript"] } },
          step_2: { status: "COMPLETED", output: { ats_score: 87 } },
          step_3: { status: "COMPLETED", output: { text_optimized: "Pioneered architectural strategies boosting conversions." } },
          step_4: { status: "COMPLETED", output: { notification_id: "notif-abc" } }
        },
        started_at: "2026-07-02T10:14:55Z",
        completed_at: "2026-07-02T10:15:00Z",
        created_at: "2026-07-02T10:14:55Z",
        updated_at: "2026-07-02T10:15:00Z"
      },
      {
        id: "exec-2",
        workflow_id: "wf-2",
        workflow: seedWorkflows[1],
        user_id: "user-1",
        status: "PAUSED",
        trigger_source: "SCHEDULED",
        current_step_index: 1,
        context_data: { target_roles: ["Staff Engineer"] },
        steps_state: {
          step_1: { status: "COMPLETED", output: { jobs_count: 3, recommended_jobs: [{ id: "1", title: "Staff Engineer", company: "DeepMind" }] } },
          step_2: { status: "PAUSED", output: { approval_required: true, prompt: "Transmitting package to DeepMind. Approve?" } }
        },
        started_at: "2026-07-02T09:00:00Z",
        created_at: "2026-07-02T09:00:00Z",
        updated_at: "2026-07-02T09:00:05Z"
      }
    ];

    setTemplates(seedTemplates);
    setWorkflows(seedWorkflows);
    setHistory(seedHistory);
  }, []);

  // ==============================================================================
  // Action Handlers
  // ==============================================================================
  const handleImportTemplate = (template: WorkflowTemplate) => {
    const newWf: Workflow = {
      id: `wf-${Date.now()}`,
      user_id: "user-1",
      name: `Imported: ${template.name}`,
      description: template.description || "Imported automation flow",
      trigger_type: template.trigger_type as any,
      trigger_config: template.trigger_config,
      definition: template.definition as any,
      is_active: true,
      status: "ACTIVE",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    setWorkflows([newWf, ...workflows]);
    setActiveTab("workflows");
    showToast(`Successfully imported template: ${template.name}`);
  };

  const handleCreateWorkflow = () => {
    setEditingWorkflow({
      name: "",
      description: "",
      trigger_type: "MANUAL",
      trigger_config: {},
      definition: { steps: [] },
      is_active: true,
      status: "ACTIVE"
    });
    setIsBuilderOpen(true);
  };

  const handleEditWorkflow = (wf: Workflow) => {
    setEditingWorkflow({ ...wf });
    setIsBuilderOpen(true);
  };

  const handleDeleteWorkflow = (id: string) => {
    if (confirm("Are you sure you want to delete this custom workflow?")) {
      setWorkflows(workflows.filter((w) => w.id !== id));
      showToast("Workflow successfully deleted", "info");
    }
  };

  const handleSaveWorkflow = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingWorkflow || !editingWorkflow.name) return;

    if (editingWorkflow.id) {
      // Edit mode
      setWorkflows(workflows.map((w) => (w.id === editingWorkflow.id ? (editingWorkflow as Workflow) : w)));
      showToast("Workflow definition updated successfully");
    } else {
      // Create mode
      const newWf: Workflow = {
        ...(editingWorkflow as Omit<Workflow, "id">),
        id: `wf-${Date.now()}`,
        user_id: "user-1",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      setWorkflows([newWf, ...workflows]);
      showToast("Custom workflow registered");
    }
    setIsBuilderOpen(false);
    setEditingWorkflow(null);
  };

  const handleAddStepToEditingWorkflow = (stepType: "action" | "condition") => {
    if (!editingWorkflow) return;
    const steps = [...(editingWorkflow.definition?.steps || [])];
    const newStep = {
      id: `step_${steps.length + 1}`,
      name: `New Step ${steps.length + 1}`,
      type: stepType,
      config: {},
      ...(stepType === "action" ? { action_type: "call_ai" as const } : { condition_type: "if" as const })
    };
    setEditingWorkflow({
      ...editingWorkflow,
      definition: { steps: [...steps, newStep] }
    });
  };

  const handleTriggerWorkflowManually = (wf: Workflow) => {
    const newExec: WorkflowExecution = {
      id: `exec-${Date.now()}`,
      workflow_id: wf.id,
      workflow: wf,
      user_id: "user-1",
      status: "RUNNING",
      trigger_source: "MANUAL",
      current_step_index: 0,
      context_data: { resume_text: "Staff full stack engineer with JAX and PyTorch skills" },
      steps_state: {},
      started_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    setHistory([newExec, ...history]);
    setSelectedExecution(newExec);
    setActiveTab("history");
    showToast(`Workflow execution triggered: ${wf.name}`);

    // Simulate async execution processing
    setTimeout(() => {
      const logsSeed: WorkflowLog[] = [
        { id: "1", execution_id: newExec.id, step_name: "Engine", level: "INFO", message: "Workflow manual execution started.", timestamp: new Date().toISOString() },
        { id: "2", execution_id: newExec.id, step_name: "Validate Content", level: "INFO", message: "Compiling variables template: Substituting {{context.resume_text}}.", timestamp: new Date().toISOString() },
        { id: "3", execution_id: newExec.id, step_name: "AI Keywords Optimization", level: "SUCCESS", message: "AI response parsed. Estimated LLM tokens prompt_tokens=150, completion_tokens=120, total_cost=$0.00054", timestamp: new Date().toISOString() },
        { id: "4", execution_id: newExec.id, step_name: "Notification Tray", level: "SUCCESS", message: "In-app Alert Tray notice generated.", timestamp: new Date().toISOString() },
        { id: "5", execution_id: newExec.id, step_name: "Engine", level: "SUCCESS", message: "Workflow finished all steps successfully. Done.", timestamp: new Date().toISOString() }
      ];
      setExecutionLogs(logsSeed);
      
      // Update execution status in history
      setHistory((prevHistory) =>
        prevHistory.map((item) =>
          item.id === newExec.id
            ? {
                ...item,
                status: "COMPLETED",
                completed_at: new Date().toISOString(),
                steps_state: {
                  step_1: { status: "COMPLETED", output: { word_count: 320 } },
                  step_2: { status: "COMPLETED", output: { completed: true } }
                }
              }
            : item
        )
      );
    }, 1500);
  };

  const handleApprovePausedGate = (exec: WorkflowExecution, stepId: string, approved: boolean) => {
    showToast(approved ? "User approved. Resuming pipeline..." : "User denied. Aborting execution...", approved ? "success" : "error");
    
    setHistory((prevHistory) =>
      prevHistory.map((item) =>
        item.id === exec.id
          ? {
              ...item,
              status: approved ? "COMPLETED" : "FAILED",
              completed_at: new Date().toISOString(),
              error_message: approved ? undefined : "Cancelled by user approval gate.",
              steps_state: {
                ...item.steps_state,
                [stepId]: { status: approved ? "COMPLETED" : "FAILED", output: { approved } }
              }
            }
          : item
        )
    );
    setSelectedExecution(null);
  };

  const filteredWorkflows = workflows.filter((w) =>
    w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    w.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div id="workflow-module-container" className="space-y-8 max-w-7xl mx-auto pb-12 font-sans text-slate-100">
      
      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className={`fixed top-6 right-6 z-50 p-4 rounded-xl shadow-2xl border flex items-center space-x-3 backdrop-blur-md ${
              toast.type === "success"
                ? "bg-emerald-950/95 border-emerald-500/30 text-emerald-300"
                : toast.type === "error"
                ? "bg-red-950/95 border-red-500/30 text-red-300"
                : "bg-slate-900/95 border-slate-800 text-slate-300"
            }`}
          >
            <div className={`h-2 w-2 rounded-full ${toast.type === "success" ? "bg-emerald-400 animate-pulse" : toast.type === "error" ? "bg-red-400" : "bg-slate-400"}`} />
            <span className="text-xs font-semibold">{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-850 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-full px-3 py-1 text-xs text-emerald-400 mb-2">
            <Sparkles className="h-3.5 w-3.5 animate-pulse" />
            <span>Enterprise Workflow Engine & AI Automation Blocks</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            <WorkflowIcon className="h-8 w-8 text-emerald-400" />
            AI Automation <span className="text-emerald-400">Workflows</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Create custom trigger-action pipelines, chain recursive AI templates, schedule job matches, and hook automatic resume optimizations.
          </p>
        </div>
        
        <div className="flex items-center gap-3 shrink-0">
          <button
            id="create-wf-btn"
            onClick={handleCreateWorkflow}
            className="flex items-center space-x-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold px-4 py-2 rounded-lg text-xs transition-all shadow-lg shadow-emerald-500/10 hover:shadow-emerald-500/20"
          >
            <Plus className="h-4 w-4" />
            <span>Create Workflow</span>
          </button>
        </div>
      </div>

      {/* Primary Sub Tabs */}
      <div className="flex space-x-1 bg-slate-900/60 p-1 rounded-xl border border-slate-850 max-w-md">
        <button
          onClick={() => { setActiveTab("workflows"); setSelectedExecution(null); }}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === "workflows" ? "bg-emerald-500 text-slate-950 font-extrabold" : "text-slate-450 hover:text-slate-200"}`}
        >
          <WorkflowIcon className="h-4 w-4" />
          <span>My Workflows</span>
        </button>
        <button
          onClick={() => { setActiveTab("templates"); setSelectedExecution(null); }}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === "templates" ? "bg-emerald-500 text-slate-950 font-extrabold" : "text-slate-450 hover:text-slate-200"}`}
        >
          <BookOpen className="h-4 w-4" />
          <span>Templates Library</span>
        </button>
        <button
          onClick={() => { setActiveTab("history"); }}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === "history" ? "bg-emerald-500 text-slate-950 font-extrabold" : "text-slate-450 hover:text-slate-200"}`}
        >
          <Activity className="h-4 w-4" />
          <span>Audit Logs</span>
        </button>
      </div>

      {/* Main Container Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Main Panel Content Area */}
        <div className={`${selectedExecution ? "lg:col-span-7" : "lg:col-span-12"} transition-all duration-300 space-y-6`}>
          
          {/* SEARCH BAR on My Workflows Tab */}
          {activeTab === "workflows" && (
            <div className="relative">
              <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-550" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search workflows by keyword or custom description..."
                className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-850 rounded-xl text-xs text-white placeholder-slate-550 focus:outline-none focus:border-emerald-500/50 transition-all font-medium"
              />
            </div>
          )}

          {/* TAB 1: WORKFLOWS LIST */}
          {activeTab === "workflows" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredWorkflows.length > 0 ? (
                filteredWorkflows.map((wf) => (
                  <motion.div
                    key={wf.id}
                    layoutId={`wf-card-${wf.id}`}
                    className="bg-slate-900 border border-slate-850 rounded-2xl p-6 hover:border-slate-800 transition-all flex flex-col justify-between h-64 shadow-xl shadow-slate-950/20"
                  >
                    <div>
                      <div className="flex justify-between items-start mb-4">
                        <span className={`text-[9px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-full ${
                          wf.trigger_type === "EVENT_DRIVEN"
                            ? "bg-emerald-950 border border-emerald-500/20 text-emerald-400"
                            : wf.trigger_type === "SCHEDULED"
                            ? "bg-amber-950 border border-amber-500/20 text-amber-400"
                            : "bg-blue-950 border border-blue-500/20 text-blue-400"
                        }`}>
                          {wf.trigger_type === "EVENT_DRIVEN" ? "Event Trigger" : wf.trigger_type === "SCHEDULED" ? "Scheduler Cron" : "Manual REST API"}
                        </span>
                        
                        <div className="flex items-center space-x-1.5">
                          <button
                            onClick={() => handleEditWorkflow(wf)}
                            className="p-1.5 hover:text-white text-slate-450 hover:bg-slate-850 rounded"
                            title="Edit properties"
                          >
                            <Settings className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteWorkflow(wf.id)}
                            className="p-1.5 hover:text-red-400 text-slate-450 hover:bg-slate-850 rounded"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      <h3 className="text-sm font-extrabold text-white tracking-tight mb-2">{wf.name}</h3>
                      <p className="text-xs text-slate-450 leading-relaxed line-clamp-3">{wf.description}</p>
                    </div>

                    <div className="border-t border-slate-850 pt-4 flex items-center justify-between mt-4">
                      <div className="flex items-center text-[10px] text-slate-500 font-mono">
                        <Clock className="h-3 w-3 mr-1" />
                        <span>Last run: {wf.last_run_at ? new Date(wf.last_run_at).toLocaleTimeString() : "Never"}</span>
                      </div>

                      <button
                        onClick={() => handleTriggerWorkflowManually(wf)}
                        className="flex items-center space-x-1 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500 border border-emerald-500/25 hover:border-emerald-500 hover:text-slate-950 text-emerald-400 font-extrabold rounded-lg text-[10px] transition-all"
                      >
                        <Play className="h-3 w-3 fill-current" />
                        <span>Execute</span>
                      </button>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="col-span-full py-16 text-center border-2 border-dashed border-slate-850 rounded-2xl bg-slate-900/20">
                  <WorkflowIcon className="h-10 w-10 text-slate-650 mx-auto mb-3" />
                  <span className="text-xs font-bold text-slate-400 block">No matching automation workflows found</span>
                  <span className="text-[10px] text-slate-550 block mt-1">Configure your first automation trigger sequence from scratch or load a template blueprint.</span>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: SYSTEM TEMPLATES */}
          {activeTab === "templates" && (
            <div className="space-y-6">
              {templates.map((tpl) => (
                <div
                  key={tpl.id}
                  className="bg-slate-900 border border-slate-850 rounded-2xl p-6 hover:border-slate-800 transition-all flex flex-col md:flex-row md:items-center justify-between gap-6"
                >
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-[9px] font-mono font-bold uppercase px-2.5 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                        {tpl.category}
                      </span>
                    </div>
                    <h3 className="text-sm font-extrabold text-white tracking-tight">{tpl.name}</h3>
                    <p className="text-xs text-slate-450 leading-relaxed max-w-2xl">{tpl.description}</p>
                    
                    {/* Visual indicators of the steps inside template */}
                    <div className="flex flex-wrap items-center gap-2 pt-2">
                      {tpl.definition.steps?.map((st: any, i: number) => (
                        <React.Fragment key={st.id}>
                          {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-slate-600" />}
                          <span className="text-[10px] bg-slate-950 border border-slate-850 rounded px-2 py-1 font-mono text-slate-400 flex items-center">
                            <Sliders className="h-2.5 w-2.5 mr-1 text-emerald-500" />
                            {st.name}
                          </span>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => handleImportTemplate(tpl)}
                    className="shrink-0 flex items-center space-x-1 px-4 py-2 bg-emerald-500 text-slate-950 font-extrabold rounded-lg text-xs hover:bg-emerald-400 transition-all"
                  >
                    <FolderSync className="h-4.5 w-4.5" />
                    <span>Load Template</span>
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* TAB 3: EXECUTION AUDIT HISTORY */}
          {activeTab === "history" && (
            <div className="bg-slate-900 border border-slate-850 rounded-2xl overflow-hidden shadow-xl shadow-slate-950/30">
              <div className="p-5 border-b border-slate-850">
                <h3 className="text-sm font-extrabold text-white flex items-center">
                  <Activity className="h-4.5 w-4.5 text-emerald-400 mr-2" /> Orchestrator Job Tracker logs
                </h3>
              </div>
              
              <div className="divide-y divide-slate-850">
                {history.length > 0 ? (
                  history.map((exec) => (
                    <div
                      key={exec.id}
                      onClick={() => setSelectedExecution(exec)}
                      className={`p-5 flex items-center justify-between gap-4 hover:bg-slate-850/30 cursor-pointer transition-colors ${selectedExecution?.id === exec.id ? "bg-slate-850/50" : ""}`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-white">{exec.workflow?.name || "Manual Integration"}</span>
                          <span className="text-[9px] text-slate-500 font-mono">#{exec.id.substring(5, 12)}</span>
                        </div>
                        
                        <div className="flex items-center gap-3 text-[10px] text-slate-450 font-mono">
                          <span className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {exec.started_at ? new Date(exec.started_at).toLocaleTimeString() : "No timestamp"}
                          </span>
                          <span>•</span>
                          <span>Source: {exec.trigger_source}</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-[9px] uppercase font-bold tracking-wider ${
                          exec.status === "COMPLETED"
                            ? "bg-emerald-950 border border-emerald-500/20 text-emerald-400"
                            : exec.status === "PAUSED"
                            ? "bg-amber-950 border border-amber-500/20 text-amber-400"
                            : exec.status === "RUNNING"
                            ? "bg-blue-950 border border-blue-500/20 text-blue-400"
                            : "bg-red-950 border border-red-500/20 text-red-400"
                        }`}>
                          <div className={`h-1.5 w-1.5 rounded-full ${exec.status === "COMPLETED" ? "bg-emerald-400" : exec.status === "PAUSED" ? "bg-amber-400 animate-pulse" : exec.status === "RUNNING" ? "bg-blue-400 animate-ping" : "bg-red-400"}`} />
                          <span>{exec.status}</span>
                        </span>
                        
                        <ChevronRight className="h-4 w-4 text-slate-550" />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-16 text-center text-slate-500">
                    <span>No workflow jobs have been run yet</span>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>

        {/* Dynamic Execution Monitor (Displays in parallel with history) */}
        {selectedExecution && activeTab === "history" && (
          <div className="lg:col-span-5 bg-slate-900 border border-emerald-500/10 rounded-2xl p-6 space-y-6 shadow-2xl shadow-emerald-950/5 relative">
            <button
              onClick={() => setSelectedExecution(null)}
              className="absolute top-4 right-4 text-slate-500 hover:text-white text-xs font-bold"
            >
              Close panel
            </button>
            
            <div>
              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest font-mono">Active Job Analytics</span>
              <h3 className="text-md font-extrabold text-white mt-1 leading-tight">{selectedExecution.workflow?.name}</h3>
              <p className="text-xs text-slate-550 mt-1">Status: <span className="text-slate-300 font-bold">{selectedExecution.status}</span></p>
            </div>

            {/* AWAITING USER APPROVAL BANNER */}
            {selectedExecution.status === "PAUSED" && (
              <div className="bg-amber-950/45 border border-amber-500/20 rounded-xl p-4 space-y-3">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="text-xs font-bold text-amber-300">Approval Gate Pending</span>
                    <p className="text-[11px] text-slate-400 leading-normal">
                      This workflow contains an active interactive gate requiring manual validation before transmitting packet data.
                    </p>
                  </div>
                </div>

                <div className="flex space-x-2 pt-1 justify-end">
                  <button
                    onClick={() => handleApprovePausedGate(selectedExecution, "step_2", false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-300 font-bold rounded-lg text-[10px] transition-colors"
                  >
                    Deny submission
                  </button>
                  <button
                    onClick={() => handleApprovePausedGate(selectedExecution, "step_2", true)}
                    className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold rounded-lg text-[10px] transition-all"
                  >
                    Approve Submission
                  </button>
                </div>
              </div>
            )}

            {/* FLOW CHART DIAGRAM (Sequential Progress Tracker) */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Step Sequence Status</h4>
              
              <div className="space-y-3 pl-2">
                {selectedExecution.workflow?.definition.steps.map((st: any, idx: number) => {
                  const state = selectedExecution.steps_state[st.id] || { status: "PENDING" };
                  const isCurrent = selectedExecution.current_step_index === idx;

                  return (
                    <div key={st.id} className="relative flex items-start gap-3 pl-4 border-l border-slate-800 pb-2 last:pb-0">
                      {/* Connector Line Dots */}
                      <div className={`absolute -left-[5.5px] top-1.5 h-2.5 w-2.5 rounded-full border-2 ${
                        state.status === "COMPLETED"
                          ? "bg-emerald-500 border-emerald-950"
                          : state.status === "FAILED"
                          ? "bg-red-500 border-red-950"
                          : isCurrent
                          ? "bg-blue-500 border-blue-950 animate-pulse"
                          : "bg-slate-850 border-slate-900"
                      }`} />

                      <div className="flex-1 space-y-1 bg-slate-950/40 p-3 rounded-xl border border-slate-850/60">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold text-slate-200">{st.name}</span>
                          <span className={`text-[9px] font-mono font-bold ${
                            state.status === "COMPLETED"
                              ? "text-emerald-400"
                              : state.status === "FAILED"
                              ? "text-red-400"
                              : isCurrent
                              ? "text-blue-400"
                              : "text-slate-550"
                          }`}>
                            {state.status}
                          </span>
                        </div>
                        
                        {st.action_type && (
                          <div className="text-[9px] uppercase tracking-widest text-slate-500 font-bold">
                            {st.action_type.replace("_", " ")}
                          </div>
                        )}
                        
                        {st.config?.prompt && (
                          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-850 mt-2">
                            <span className="text-[10px] text-slate-400 leading-normal block italic">
                              "{st.config.prompt}"
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* REAL-TIME CONSOLE TRACE LOGS */}
            <div className="space-y-3 border-t border-slate-850 pt-5">
              <div className="flex justify-between items-center">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
                  <Terminal className="h-4 w-4 text-emerald-400 mr-2" /> Live Trace Console logs
                </h4>
                
                <button
                  onClick={() => {
                    setIsRefreshingLogs(true);
                    setTimeout(() => setIsRefreshingLogs(false), 800);
                  }}
                  className="text-slate-550 hover:text-white p-1 hover:bg-slate-850 rounded"
                  title="Force refresh"
                >
                  <RotateCw className={`h-3 w-3 ${isRefreshingLogs ? "animate-spin" : ""}`} />
                </button>
              </div>

              <div className="bg-slate-950 border border-slate-850 rounded-xl p-4 h-48 overflow-y-auto font-mono text-[10px] text-slate-400 space-y-2">
                {executionLogs.length > 0 ? (
                  executionLogs.map((log) => (
                    <div key={log.id} className="flex gap-2 items-start leading-normal">
                      <span className="text-slate-650 shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      <span className={`font-extrabold shrink-0 ${log.level === "ERROR" ? "text-red-400" : log.level === "SUCCESS" ? "text-emerald-400" : "text-blue-400"}`}>
                        [{log.step_name}]
                      </span>
                      <span className="text-slate-300">{log.message}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-slate-600">
                    <span>Awaiting dynamic system execution trace...</span>
                  </div>
                )}
              </div>
            </div>

          </div>
        )}

      </div>

      {/* ==============================================================================
          MODAL: INTERACTIVE VISUAL WORKFLOW BUILDER
          ============================================================================== */}
      <AnimatePresence>
        {isBuilderOpen && editingWorkflow && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl relative"
            >
              <button
                type="button"
                onClick={() => setIsBuilderOpen(false)}
                className="absolute top-6 right-6 text-slate-400 hover:text-white"
              >
                Cancel
              </button>

              <h2 className="text-xl font-extrabold text-white tracking-tight mb-2">
                {editingWorkflow.id ? "Edit Workflow Definition" : "Design Custom Automation Flow"}
              </h2>
              <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                Wire triggers and link AI execution blocks or conditional routers to design customized SaaS automations.
              </p>

              <form onSubmit={handleSaveWorkflow} className="space-y-6">
                
                {/* 1. Name & Description */}
                <div className="space-y-4">
                  <div>
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Workflow Name</label>
                    <input
                      type="text"
                      required
                      value={editingWorkflow.name || ""}
                      onChange={(e) => setEditingWorkflow({ ...editingWorkflow, name: e.target.value })}
                      placeholder="e.g. Daily Job Scraper & Cover Letter Synthesizer"
                      className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Description (SaaS logs summary)</label>
                    <textarea
                      value={editingWorkflow.description || ""}
                      onChange={(e) => setEditingWorkflow({ ...editingWorkflow, description: e.target.value })}
                      placeholder="Explain what specific events this workflow automates..."
                      rows={2}
                      className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                    />
                  </div>
                </div>

                {/* 2. Triggers Setting */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Trigger Type</label>
                    <select
                      value={editingWorkflow.trigger_type || "MANUAL"}
                      onChange={(e) => setEditingWorkflow({ ...editingWorkflow, trigger_type: e.target.value as any })}
                      className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-emerald-500/50"
                    >
                      <option value="MANUAL">Manual Trigger (REST API)</option>
                      <option value="SCHEDULED">Scheduled Chronometer (Cron)</option>
                      <option value="EVENT_DRIVEN">Event Driven (System Published)</option>
                    </select>
                  </div>

                  {editingWorkflow.trigger_type === "SCHEDULED" && (
                    <div>
                      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Cron expression (UTC)</label>
                      <input
                        type="text"
                        value={editingWorkflow.trigger_config?.cron || ""}
                        onChange={(e) => setEditingWorkflow({ ...editingWorkflow, trigger_config: { cron: e.target.value } })}
                        placeholder="e.g. 0 9 * * *"
                        className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-emerald-500/50"
                      />
                    </div>
                  )}

                  {editingWorkflow.trigger_type === "EVENT_DRIVEN" && (
                    <div>
                      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">System Event ID</label>
                      <select
                        value={editingWorkflow.trigger_config?.event || "resume.uploaded"}
                        onChange={(e) => setEditingWorkflow({ ...editingWorkflow, trigger_config: { event: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-emerald-500/50"
                      >
                        <option value="resume.uploaded">resume.uploaded</option>
                        <option value="job.matched">job.matched</option>
                        <option value="interview.completed">interview.completed</option>
                      </select>
                    </div>
                  )}
                </div>

                {/* 3. Flow Sequence Editor */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Execution block sequence</label>
                    
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleAddStepToEditingWorkflow("action")}
                        className="flex items-center space-x-1 text-[10px] bg-slate-800 hover:bg-slate-750 px-2.5 py-1 rounded text-emerald-400 font-bold"
                      >
                        <PlusCircle className="h-3 w-3 mr-1" /> Add Action block
                      </button>
                      <button
                        type="button"
                        onClick={() => handleAddStepToEditingWorkflow("condition")}
                        className="flex items-center space-x-1 text-[10px] bg-slate-800 hover:bg-slate-750 px-2.5 py-1 rounded text-amber-400 font-bold"
                      >
                        <PlusCircle className="h-3 w-3 mr-1" /> Add Condition block
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3 max-h-60 overflow-y-auto border border-slate-850 bg-slate-950/30 p-4 rounded-xl">
                    {editingWorkflow.definition?.steps && editingWorkflow.definition.steps.length > 0 ? (
                      editingWorkflow.definition.steps.map((st, i) => (
                        <div key={st.id} className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-3 flex flex-col justify-between">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center space-x-2">
                              <span className="text-[10px] text-slate-600 font-mono font-bold">Step {i + 1}</span>
                              <span className={`text-[8px] uppercase tracking-wider px-2 py-0.5 rounded font-bold ${st.type === "action" ? "bg-emerald-950/40 text-emerald-400" : "bg-amber-950/40 text-amber-400"}`}>
                                {st.type}
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => {
                                const steps = editingWorkflow.definition?.steps.filter((s) => s.id !== st.id);
                                setEditingWorkflow({ ...editingWorkflow, definition: { steps } });
                              }}
                              className="text-red-400 hover:text-red-300 text-[10px]"
                            >
                              Remove block
                            </button>
                          </div>

                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <input
                                type="text"
                                required
                                value={st.name}
                                onChange={(e) => {
                                  const steps = [...(editingWorkflow.definition?.steps || [])];
                                  steps[i].name = e.target.value;
                                  setEditingWorkflow({ ...editingWorkflow, definition: { steps } });
                                }}
                                placeholder="Block descriptive name"
                                className="w-full bg-slate-900 border border-slate-850 rounded-lg px-3 py-1.5 text-xs text-white"
                              />
                            </div>

                            {st.type === "action" ? (
                              <div>
                                <select
                                  value={st.action_type || "call_ai"}
                                  onChange={(e) => {
                                    const steps = [...(editingWorkflow.definition?.steps || [])];
                                    steps[i].action_type = e.target.value as any;
                                    setEditingWorkflow({ ...editingWorkflow, definition: { steps } });
                                  }}
                                  className="w-full bg-slate-900 border border-slate-850 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
                                >
                                  <option value="call_ai">Call AI Generation (Gemini)</option>
                                  <option value="create_notification">Create Push Notification</option>
                                  <option value="send_email">Transmit Email Alert</option>
                                  <option value="call_internal_api">Local API Route Fetch</option>
                                </select>
                              </div>
                            ) : (
                              <div>
                                <select
                                  value={st.condition_type || "if"}
                                  onChange={(e) => {
                                    const steps = [...(editingWorkflow.definition?.steps || [])];
                                    steps[i].condition_type = e.target.value as any;
                                    setEditingWorkflow({ ...editingWorkflow, definition: { steps } });
                                  }}
                                  className="w-full bg-slate-900 border border-slate-850 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
                                >
                                  <option value="if">If / Else comparative branch</option>
                                  <option value="approval">Awaiting manual approval gate</option>
                                  <option value="delay">Execution timer (Delay)</option>
                                </select>
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-10 text-slate-650 text-xs">
                        <span>No sequence steps configured yet. Use the buttons above.</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-slate-850">
                  <button
                    type="button"
                    onClick={() => setIsBuilderOpen(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-slate-300 font-bold rounded-lg text-xs"
                  >
                    Discard Changes
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold rounded-lg text-xs transition-all shadow-lg shadow-emerald-500/10"
                  >
                    Save Definition
                  </button>
                </div>

              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
