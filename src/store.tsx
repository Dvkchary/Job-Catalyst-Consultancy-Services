import React, { createContext, useContext, useState, useEffect } from "react";
import {
  UserProfile,
  SubscriptionPlan,
  Subscription,
  UsageMetric,
  Invoice,
  ResumeVersion,
  ResumeTemplate,
  ATSReport,
  Job,
  AIMatchReport,
  Application,
  InterviewSession,
  AuditLog,
  FeatureFlag,
  SystemConfig
} from "./types";

// ==========================================
// Initial Core Datasets
// ==========================================

export const INITIAL_PLANS: SubscriptionPlan[] = [
  {
    id: "plan-free",
    name: "Free Trial Plan",
    code: "free",
    description: "Get started exploring career opportunities and templates.",
    price_monthly: 0,
    price_yearly: 0,
    currency: "USD",
    is_active: true,
    feature_limits: {
      ai_credits: 50,
      resume_limits: 1,
      job_match_limits: 5,
      interview_limits: 1,
      storage_bytes: 2 * 1024 * 1024,
      api_limits_per_min: 5
    }
  },
  {
    id: "plan-starter",
    name: "Starter Track",
    code: "starter",
    description: "Perfect for active candidates preparing application drafts.",
    price_monthly: 9.99,
    price_yearly: 99.9,
    currency: "USD",
    is_active: true,
    feature_limits: {
      ai_credits: 500,
      resume_limits: 3,
      job_match_limits: 25,
      interview_limits: 5,
      storage_bytes: 10 * 1024 * 1024,
      api_limits_per_min: 15
    },
    badge: "Popular"
  },
  {
    id: "plan-pro",
    name: "Professional Catalyst",
    code: "professional",
    description: "Our core suite with continuous AI iterations and interview coaching.",
    price_monthly: 19.99,
    price_yearly: 199.9,
    currency: "USD",
    is_active: true,
    feature_limits: {
      ai_credits: 2000,
      resume_limits: 10,
      job_match_limits: 100,
      interview_limits: 20,
      storage_bytes: 50 * 1024 * 1024,
      api_limits_per_min: 30
    },
    badge: "Recommended"
  },
  {
    id: "plan-premium",
    name: "Enterprise Premium",
    code: "premium",
    description: "Fully loaded tracking pipelines, API tokens, and dedicated coaching.",
    price_monthly: 49.99,
    price_yearly: 499.9,
    currency: "USD",
    is_active: true,
    feature_limits: {
      ai_credits: 10000,
      resume_limits: 50,
      job_match_limits: 1000,
      interview_limits: 100,
      storage_bytes: 500 * 1024 * 1024,
      api_limits_per_min: 100
    }
  },
  {
    id: "plan-enterprise",
    name: "Custom Enterprise",
    code: "enterprise",
    description: "Dedicated resources, infinite resumes, and high-performance routing SLA.",
    price_monthly: 299.99,
    price_yearly: 2999.0,
    currency: "USD",
    is_active: true,
    feature_limits: {
      ai_credits: 100000,
      resume_limits: 1000,
      job_match_limits: 50000,
      interview_limits: 5000,
      storage_bytes: 100 * 1024 * 1024 * 1024, // 100GB
      api_limits_per_min: 1000
    },
    badge: "Powerhouse"
  }
];

export const INITIAL_JOBS: Job[] = [
  {
    id: "job-1",
    title: "Lead AI Research Engineer",
    company: "Google DeepMind",
    logo: "https://images.unsplash.com/photo-1572021335469-31706a17aaef?w=80&fit=crop&q=80",
    location: "London, UK (Hybrid)",
    type: "Full-Time",
    description: "Lead foundational research and fine-tuning experiments on state-of-the-art multimodal generative assistants.",
    requirements: [
      "PhD/MS in Computer Science, Machine Learning, or related field.",
      "5+ years of production experience scaling distributed LLM training pipelines.",
      "Expert knowledge of PyTorch, JAX, and transformer architectures."
    ],
    skills_required: ["Python", "PyTorch", "JAX", "Transformers", "Distributed Systems"],
    salary_range: "$180,000 - $250,000",
    source: "Google Careers",
    posted_at: "2 hours ago"
  },
  {
    id: "job-2",
    title: "Senior Full-Stack Product Developer",
    company: "Stripe",
    logo: "https://images.unsplash.com/photo-1549813069-f913609b4d46?w=80&fit=crop&q=80",
    location: "San Francisco, CA (Remote)",
    type: "Full-Time",
    description: "Design and implement billing pipelines, customer portal upgrades, and checkout widget optimizations.",
    requirements: [
      "Extensive production expertise in React, TypeScript, and Node.js.",
      "3+ years managing SaaS billing engines, ledger setups, or stripe-node sdk.",
      "Passionate about pixel-perfect interactive aesthetics."
    ],
    skills_required: ["TypeScript", "React", "Node.js", "Stripe API", "TailwindCSS"],
    salary_range: "$160,000 - $210,000",
    source: "Stripe Board",
    posted_at: "Yesterday"
  },
  {
    id: "job-3",
    title: "Associate Product Manager",
    company: "Airbnb",
    logo: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=80&fit=crop&q=80",
    location: "New York, NY (Hybrid)",
    type: "Full-Time",
    description: "Collaborate with cross-functional design and data science teams to optimize traveler search ranking interfaces.",
    requirements: [
      "BS in engineering, design, business or equivalent field.",
      "Strong analytical skills, proficient in SQL and A/B testing frameworks.",
      "Prior product internship or product design experience."
    ],
    skills_required: ["Product Strategy", "A/B Testing", "SQL", "User Analytics", "Figma"],
    salary_range: "$110,000 - $140,000",
    source: "Airbnb Portal",
    posted_at: "3 days ago"
  }
];

export const INITIAL_TEMPLATES: ResumeTemplate[] = [
  {
    id: "tpl-1",
    name: "Standard Swiss Minimalist",
    category: "Professional",
    is_published: true,
    description: "An elegant serif design engineered with standard single-column alignment for high-performance ATS indexing.",
    colors: { primary: "#111827", secondary: "#4b5563", text: "#1f2937" }
  },
  {
    id: "tpl-2",
    name: "Tech-Forward JetBrains",
    category: "Technical",
    is_published: true,
    description: "A dual-column modern display paired with dark emerald header accents and spacious code font elements.",
    colors: { primary: "#047857", secondary: "#1f2937", text: "#374151" }
  },
  {
    id: "tpl-3",
    name: "Editorial Warm Playfair",
    category: "Creative",
    is_published: true,
    description: "High-contrast classic styling using elegant serif displays and horizontal separator tags ideal for executives.",
    colors: { primary: "#7c2d12", secondary: "#3f2f2f", text: "#1f2937" }
  }
];

// ==========================================
// Context State Interface
// ==========================================

interface AppState {
  // Authentication State
  user: UserProfile | null;
  mfaCodeNeeded: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  verifyMfa: (code: string) => boolean;
  verifyEmailLink: () => void;
  resetPasswordRequest: (email: string) => boolean;

  // Navigation State
  currentTab: "landing" | "auth" | "dashboard";
  activeDashboardSubTab:
    | "overview"
    | "resume"
    | "ats"
    | "jobs"
    | "matcher"
    | "tracker"
    | "interview"
    | "coach"
    | "admin"
    | "billing";
  setCurrentTab: (tab: "landing" | "auth" | "dashboard") => void;
  setActiveDashboardSubTab: (sub: any) => void;

  // Subscription & Billing State
  subscription: Subscription;
  plans: SubscriptionPlan[];
  usage: UsageMetric;
  invoices: Invoice[];
  activePlan: SubscriptionPlan;
  upgradeSubscription: (planCode: "free" | "starter" | "professional" | "premium" | "enterprise", period: "monthly" | "yearly") => void;
  pauseSubscription: () => void;
  cancelSubscription: () => void;
  applyCouponCode: (code: string) => { success: boolean; discount: number; message: string };
  appliedDiscount: number;

  // Resume State
  resumeVersions: ResumeVersion[];
  selectedResumeVersion: ResumeVersion | null;
  templates: ResumeTemplate[];
  saveResumeVersion: (version: ResumeVersion) => void;
  addResumeVersion: (name: string) => void;
  setSelectedResumeVersion: (version: ResumeVersion | null) => void;

  // ATS Analysis State
  atsReport: ATSReport | null;
  runAtsAnalysis: (resumeText: string, jobDesc: string) => void;
  atsHistory: { timestamp: string; score: number; title: string }[];

  // Jobs State
  jobs: Job[];
  savedJobIds: string[];
  toggleSaveJob: (id: string) => void;
  searchJobs: (query: string, type: string) => Job[];

  // Matcher State
  matchReport: AIMatchReport | null;
  runAiMatcher: (jobId: string) => void;

  // Application Tracker State
  applications: Application[];
  moveApplicationStatus: (appId: string, status: "applied" | "screening" | "interviewing" | "offered" | "rejected") => void;
  addApplication: (jobId: string, jobTitle: string, company: string) => void;
  addRecruiterNote: (appId: string, note: string) => void;

  // Interview Coach State
  interviews: InterviewSession[];
  activeInterview: InterviewSession | null;
  startMockInterview: (jobTitle: string, company: string, mode: "audio" | "text") => void;
  sendInterviewMessage: (text: string) => void;
  completeInterview: () => void;

  // Notifications State
  notifications: { id: string; title: string; message: string; is_read: boolean; priority: "Low" | "Medium" | "High"; timestamp: string }[];
  markNotificationsAsRead: () => void;
  notificationPreferences: { enable_email: boolean; enable_in_app: boolean; quiet_hours: boolean };
  updateNotificationPreferences: (prefs: any) => void;

  // Admin Controls State
  adminUsers: UserProfile[];
  adminConfigs: SystemConfig[];
  adminFlags: FeatureFlag[];
  adminLogs: AuditLog[];
  updateAdminUserStatus: (userId: string, status: any) => void;
  updateAdminUserRoles: (userId: string, roles: string[]) => void;
  updateSystemConfig: (key: string, value: any) => void;
  updateFeatureFlag: (id: string, updates: Partial<FeatureFlag>) => void;
  addAuditLog: (category: string, action: string, description: string) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Navigation
  const [currentTab, setCurrentTab] = useState<"landing" | "auth" | "dashboard">("landing");
  const [activeDashboardSubTab, setActiveDashboardSubTab] = useState<any>("overview");

  // Authentication State
  const [user, setUser] = useState<UserProfile | null>(() => {
    // Default admin user seeded for direct exploration
    return {
      id: "user-admin",
      username: "enterprise_admin",
      email: "6309vs@gmail.com",
      status: "ACTIVE",
      email_verified: true,
      mfa_enabled: false,
      roles: ["ADMIN", "USER"],
      created_at: new Date().toISOString()
    };
  });
  const [mfaCodeNeeded, setMfaCodeNeeded] = useState(false);

  // Subscription state
  const [plans] = useState<SubscriptionPlan[]>(INITIAL_PLANS);
  const [activePlan, setActivePlan] = useState<SubscriptionPlan>(INITIAL_PLANS[2]); // Professional by default
  const [subscription, setSubscription] = useState<Subscription>({
    id: "sub-123",
    user_id: "user-admin",
    plan_id: "plan-pro",
    status: "active",
    billing_period: "monthly",
    current_period_start: new Date().toISOString(),
    current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    cancel_at_period_end: false,
    payment_provider: "stripe"
  });

  const [usage, setUsage] = useState<UsageMetric>({
    ai_credits_used: 480,
    resumes_parsed: 3,
    ats_analyses: 6,
    interview_sessions: 2,
    job_matches: 12,
    api_calls: 140,
    storage_bytes: 8 * 1024 * 1024
  });

  const [appliedDiscount, setAppliedDiscount] = useState(0);

  const [invoices, setInvoices] = useState<Invoice[]>([
    {
      id: "inv-001",
      invoice_number: "INV-2026-001",
      status: "paid",
      subtotal: 19.99,
      tax: 1.6,
      discount: 0.0,
      total: 21.59,
      currency: "USD",
      billing_email: "6309vs@gmail.com",
      created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: "inv-002",
      invoice_number: "INV-2026-002",
      status: "paid",
      subtotal: 19.99,
      tax: 1.6,
      discount: 5.0,
      total: 16.59,
      currency: "USD",
      billing_email: "6309vs@gmail.com",
      created_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString()
    }
  ]);

  // Resume builder state
  const [resumeVersions, setResumeVersions] = useState<ResumeVersion[]>([
    {
      id: "ver-1",
      name: "Master AI Research CV",
      updated_at: "Today, 10:15 AM",
      sections: [
        {
          id: "sec-p",
          type: "personal",
          title: "Personal Information",
          content: { name: "Alex Catalyst", email: "alex@career.io", phone: "+1 555-0199", github: "github.com/catalyst" }
        },
        {
          id: "sec-s",
          type: "summary",
          title: "Executive Summary",
          content: "Experienced Machine Learning Researcher pioneering distributed optimization techniques and generative transformer alignment."
        },
        {
          id: "sec-e",
          type: "experience",
          title: "Professional Experience",
          content: [
            { role: "Senior NLP Engineer", company: "AeroAI Lab", duration: "2024 - Present", bullets: ["Reduced token routing overhead by 22% using custom expert-gate heuristics.", "Led development of fine-tuning pipelines utilizing low-rank adaptors."] }
          ]
        },
        {
          id: "sec-k",
          type: "skills",
          title: "Technical Core Skills",
          content: ["Python", "PyTorch", "JAX", "Transformers", "SQL", "TailwindCSS", "Node.js"]
        }
      ]
    },
    {
      id: "ver-2",
      name: "Stripe Product Engineer Draft",
      updated_at: "3 days ago",
      sections: [
        {
          id: "sec-p2",
          type: "personal",
          title: "Personal Details",
          content: { name: "Alex Catalyst", email: "alex@career.io", phone: "+1 555-0199" }
        },
        {
          id: "sec-s2",
          type: "summary",
          title: "Career Summary",
          content: "Full-Stack developer focused on SaaS payment flows, pixel-perfect layout architectures, and interactive client engines."
        }
      ]
    }
  ]);
  const [selectedResumeVersion, setSelectedResumeVersion] = useState<ResumeVersion | null>(resumeVersions[0]);

  // ATS state
  const [atsReport, setAtsReport] = useState<ATSReport | null>(null);
  const [atsHistory, setAtsHistory] = useState<{ timestamp: string; score: number; title: string }[]>([
    { timestamp: "Yesterday, 4:00 PM", score: 82, title: "Master AI Research CV vs Google Research Lead" },
    { timestamp: "3 days ago", score: 68, title: "Stripe Draft vs Stripe Product Engineer" }
  ]);

  // Jobs state
  const [jobs, setJobs] = useState<Job[]>(INITIAL_JOBS);
  const [savedJobIds, setSavedJobIds] = useState<string[]>(["job-1"]);

  // AI Matcher state
  const [matchReport, setMatchReport] = useState<AIMatchReport | null>(null);

  // Application tracker
  const [applications, setApplications] = useState<Application[]>([
    {
      id: "app-1",
      job_id: "job-1",
      job_title: "Lead AI Research Engineer",
      company: "Google DeepMind",
      status: "interviewing",
      applied_date: "June 25, 2026",
      notes: ["Recruiter call was stellar.", "Hiring manager panel scheduled for next Monday."],
      recruiters: [{ name: "Sarah Connor", contact: "sconnor@deepmind.com" }],
      timeline: [
        { title: "Applied", date: "June 25, 2026", description: "Successfully routed via JobCatalyst portal." },
        { title: "Screening Passed", date: "June 27, 2026", description: "Completed introductory coding challenge with 100% test completion rate." },
        { title: "Interview Scheduled", date: "June 29, 2026", description: "HM round scheduled for Monday." }
      ]
    },
    {
      id: "app-2",
      job_id: "job-2",
      job_title: "Senior Full-Stack Product Developer",
      company: "Stripe",
      status: "applied",
      applied_date: "Yesterday",
      notes: [],
      recruiters: [],
      timeline: [{ title: "Applied", date: "Yesterday" }]
    }
  ]);

  // Mock interviews list
  const [interviews, setInterviews] = useState<InterviewSession[]>([
    {
      id: "int-1",
      job_title: "Lead AI Research Engineer",
      company: "Google DeepMind",
      mode: "text",
      transcript: [
        { sender: "coach", text: "Welcome! To begin, how would you approach optimizing memory consumption when scaling LLM contexts to 100k tokens?", timestamp: "10:00 AM" },
        { sender: "candidate", text: "I would utilize FlashAttention-3 alongside pipeline parallelism and activation checkpointing to avoid redundant tensor allocations.", timestamp: "10:02 AM" }
      ],
      score: 88,
      feedback: {
        clarity: 9,
        relevance: 9,
        depth: 8.5,
        general_remarks: "Exceptional explanation of tensor state. Demonstrates expert level practical expertise.",
        actionable_points: [
          "Explain the trade-offs of FlashAttention memory vs floating point ops.",
          "Optionally discuss Ring Attention protocols for extremely extended limits."
        ]
      },
      created_at: "June 28, 2026"
    }
  ]);
  const [activeInterview, setActiveInterview] = useState<InterviewSession | null>(null);

  // System Audit & Admin Portal States
  const [adminUsers, setAdminUsers] = useState<UserProfile[]>([
    { id: "user-admin", username: "enterprise_admin", email: "6309vs@gmail.com", status: "ACTIVE", email_verified: true, mfa_enabled: false, roles: ["ADMIN", "USER"], created_at: "2026-05-10" },
    { id: "user-002", username: "johndoe", email: "john@test.com", status: "ACTIVE", email_verified: true, mfa_enabled: true, roles: ["USER"], created_at: "2026-06-01" },
    { id: "user-003", username: "alice_developer", email: "alice@coder.com", status: "PENDING", email_verified: false, mfa_enabled: false, roles: ["USER"], created_at: "2026-06-20" },
    { id: "user-004", username: "spammer_99", email: "spam@block.com", status: "SUSPENDED", email_verified: true, mfa_enabled: false, roles: ["USER"], created_at: "2026-06-15" }
  ]);

  const [adminConfigs, setAdminConfigs] = useState<SystemConfig[]>([
    { id: "cfg-1", config_key: "gemini_api_key_masked", category: "Environment", config_value: "AIzaSyD...xxxx", description: "Primary model API key proxy settings" },
    { id: "cfg-2", config_key: "smtp_host", category: "Email", config_value: "smtp.sendgrid.net", description: "SMTP relay hostname" },
    { id: "cfg-3", config_key: "redis_cache_expiry_seconds", category: "Redis", config_value: 3600, description: "Redis volatile key cache TTL" }
  ]);

  const [adminFlags, setAdminFlags] = useState<FeatureFlag[]>([
    { id: "flag-1", name: "enable_live_voice_mock_interviews", description: "Enables Gemini Audio live speech analytics streams.", is_enabled: true, rollout_percentage: 100 },
    { id: "flag-2", name: "enable_enterprise_teams_collaboration", description: "Allows shared workspace document collaboration matrices.", is_enabled: false, rollout_percentage: 20 },
    { id: "flag-3", name: "enable_ats_instant_improvement_hints", description: "Shows line-by-line quick fixes in the resume compiler view.", is_enabled: true, rollout_percentage: 100 }
  ]);

  const [adminLogs, setAdminLogs] = useState<AuditLog[]>([
    { id: "log-1", user_id: "user-admin", username: "enterprise_admin", category: "Admin Action", action: "UPDATE_SYSTEM_CONFIG", description: "Modified Redis cache expiry seconds config value.", created_at: new Date(Date.now() - 360000).toISOString() },
    { id: "log-2", user_id: "user-admin", username: "enterprise_admin", category: "Security Event", action: "OVERRIDE_PASSWORD", description: "Triggered administrative bypass password override for user: johndoe.", created_at: new Date(Date.now() - 7200000).toISOString() },
    { id: "log-3", user_id: "user-002", username: "johndoe", category: "User Action", action: "DOWNLOAD_RESUME", description: "Downloaded resume PDF version Master CV.", created_at: new Date(Date.now() - 15000000).toISOString() }
  ]);

  // Notifications
  const [notifications, setNotifications] = useState<any[]>([
    { id: "notif-1", title: "New Job Match Found", message: "Google DeepMind posted: Lead AI Research Engineer matches 92% of your CV parameters.", is_read: false, priority: "High", timestamp: "1 hour ago" },
    { id: "notif-2", title: "System Scheduled Upkeep", message: "JobCatalyst database clusters will conduct automatic versioning migrations tomorrow at 4:00 AM UTC.", is_read: true, priority: "Low", timestamp: "Yesterday" }
  ]);

  const [notificationPreferences, setNotificationPreferences] = useState({
    enable_email: true,
    enable_in_app: true,
    quiet_hours: false
  });

  // ==========================================
  // Core Actions & State Reducers
  // ==========================================

  // Authentication Flows
  const login = async (email: string, password: string): Promise<boolean> => {
    // Check if the user is our pre-configured admin or user
    if (email === "6309vs@gmail.com" || email === "admin@test.com") {
      const targetUser: UserProfile = {
        id: "user-admin",
        username: "enterprise_admin",
        email: email,
        status: "ACTIVE",
        email_verified: true,
        mfa_enabled: false,
        roles: ["ADMIN", "USER"],
        created_at: new Date().toISOString()
      };
      setUser(targetUser);
      addAuditLog("Security Event", "USER_LOGIN", `Admin user successfully authenticated as ${targetUser.username}.`);
      return true;
    } else {
      const newUser: UserProfile = {
        id: "user-" + Math.random().toString(36).substr(2, 9),
        username: email.split("@")[0],
        email: email,
        status: "ACTIVE",
        email_verified: false,
        mfa_enabled: false,
        roles: ["USER"],
        created_at: new Date().toISOString()
      };
      setUser(newUser);
      addAuditLog("Security Event", "USER_LOGIN", `User authenticated as ${newUser.username}.`);
      return true;
    }
  };

  const register = async (username: string, email: string, password: string): Promise<boolean> => {
    const newUser: UserProfile = {
      id: "user-" + Math.random().toString(36).substr(2, 9),
      username: username,
      email: email,
      status: "ACTIVE",
      email_verified: false,
      mfa_enabled: false,
      roles: ["USER"],
      created_at: new Date().toISOString()
    };
    setUser(newUser);
    addAuditLog("Security Event", "USER_REGISTRATION", `New user created: ${username} (${email}).`);
    return true;
  };

  const logout = () => {
    if (user) {
      addAuditLog("Security Event", "USER_LOGOUT", `User ${user.username} logged out.`);
    }
    setUser(null);
    setCurrentTab("landing");
  };

  const verifyMfa = (code: string): boolean => {
    if (code === "123456" && user) {
      const updated = { ...user, mfa_enabled: true };
      setUser(updated);
      addAuditLog("Security Event", "MFA_VERIFIED", `MFA configuration confirmed successfully for ${user.username}.`);
      return true;
    }
    return false;
  };

  const verifyEmailLink = () => {
    if (user) {
      setUser({ ...user, email_verified: true });
      addAuditLog("Security Event", "EMAIL_VERIFICATION", `Email verification parsed for ${user.username}.`);
    }
  };

  const resetPasswordRequest = (email: string) => {
    addAuditLog("Security Event", "PASSWORD_RESET_REQUESTED", `Password recovery payload compiled for ${email}.`);
    return true;
  };

  // Subscription Operations
  const upgradeSubscription = (planCode: any, period: "monthly" | "yearly") => {
    const matchedPlan = plans.find((p) => p.code === planCode);
    if (matchedPlan) {
      setActivePlan(matchedPlan);
      setSubscription({
        ...subscription,
        plan_id: matchedPlan.id,
        billing_period: period,
        status: "active",
        current_period_start: new Date().toISOString(),
        current_period_end: new Date(Date.now() + (period === "monthly" ? 30 : 365) * 24 * 60 * 60 * 1000).toISOString()
      });

      // Inject a dynamic paid invoice simulation
      const calculatedSubtotal = period === "monthly" ? matchedPlan.price_monthly : matchedPlan.price_yearly;
      const discountAmount = Math.round(calculatedSubtotal * appliedDiscount * 100) / 100;
      const calculatedTotal = Math.round((calculatedSubtotal - discountAmount) * 1.08 * 100) / 100;

      const newInvoice: Invoice = {
        id: "inv-" + Math.floor(Math.random() * 1000),
        invoice_number: `INV-2026-` + Math.floor(100 + Math.random() * 900),
        status: "paid",
        subtotal: calculatedSubtotal,
        tax: Math.round(calculatedSubtotal * 0.08 * 100) / 100,
        discount: discountAmount,
        total: calculatedTotal,
        currency: "USD",
        billing_email: user?.email || "billing@saas.io",
        created_at: new Date().toISOString()
      };
      setInvoices([newInvoice, ...invoices]);

      addAuditLog("Admin Action", "PLAN_UPGRADE", `User upgraded subscription plan to: ${matchedPlan.name} (${period}).`);
    }
  };

  const pauseSubscription = () => {
    setSubscription({ ...subscription, status: "paused" });
    addAuditLog("Admin Action", "PLAN_PAUSE", "Subscription temporarily paused.");
  };

  const cancelSubscription = () => {
    setSubscription({ ...subscription, cancel_at_period_end: true });
    addAuditLog("Admin Action", "PLAN_CANCEL_TOGGLE", "Subscription slated to terminate at period end.");
  };

  const applyCouponCode = (code: string) => {
    const formatted = code.toUpperCase();
    if (formatted === "DISCOUNT20") {
      setAppliedDiscount(0.2);
      return { success: true, discount: 20, message: "20% discount applied to upcoming billing calculations!" };
    } else if (formatted === "FREEPROMO") {
      setAppliedDiscount(1.0);
      return { success: true, discount: 100, message: "100% discount applied successfully!" };
    }
    return { success: false, discount: 0, message: "Invalid or expired promotional code." };
  };

  // Resumes
  const saveResumeVersion = (version: ResumeVersion) => {
    const updated = resumeVersions.map((v) => (v.id === version.id ? { ...version, updated_at: "Just now" } : v));
    setResumeVersions(updated);
    setSelectedResumeVersion(version);
    setUsage((prev) => ({ ...prev, resumes_parsed: prev.resumes_parsed + 1 }));
    addAuditLog("User Action", "SAVE_RESUME", `Saved resume layout modifications for: ${version.name}.`);
  };

  const addResumeVersion = (name: string) => {
    const newVersion: ResumeVersion = {
      id: "ver-" + Math.random().toString(36).substr(2, 9),
      name: name,
      updated_at: "Just now",
      sections: JSON.parse(JSON.stringify(resumeVersions[0].sections)) // Copy standard structure
    };
    setResumeVersions([...resumeVersions, newVersion]);
    setSelectedResumeVersion(newVersion);
    addAuditLog("User Action", "CREATE_RESUME_VERSION", `Compiled resume variant named: ${name}.`);
  };

  // ATS Analysis
  const runAtsAnalysis = (resumeText: string, jobDesc: string) => {
    setUsage((prev) => ({ ...prev, ats_analyses: prev.ats_analyses + 1, ai_credits_used: prev.ai_credits_used + 150 }));
    
    // Simulate smart AI evaluation criteria based on prompt keywords
    let calculatedScore = 72;
    const isTech = resumeText.toLowerCase().includes("pytorch") || resumeText.toLowerCase().includes("python");
    if (isTech) calculatedScore += 16;
    if (jobDesc.toLowerCase().includes("senior") || jobDesc.toLowerCase().includes("lead")) calculatedScore -= 5;
    calculatedScore = Math.min(100, Math.max(20, calculatedScore));

    const mockReport: ATSReport = {
      score: calculatedScore,
      keywords_found: isTech ? ["Python", "PyTorch", "JAX", "Transformers"] : ["Communication", "Product Management", "A/B Testing"],
      keywords_missing: ["CUDA Optimizations", "Distributed Memory Clusters", "CI/CD Orchestration", "MLflow"],
      recommendations: [
        "Include quantitative output stats (e.g., 'Reduced inference latency by 18%').",
        "Append missing keyword competencies in your 'Technical Skills' grid.",
        "Refine layout structures to ensure compliance with strict XML index parsing constraints."
      ],
      structural_feedback: {
        has_contact_info: true,
        has_summary: true,
        has_experience: true,
        has_education: true,
        has_skills: true,
        formatting_issues: ["Slightly tight line heights (recommend 1.15 minimum spacing)."]
      }
    };

    setAtsReport(mockReport);
    setAtsHistory([
      { timestamp: "Just now", score: calculatedScore, title: `ATS Scan Result (${calculatedScore}%)` },
      ...atsHistory
    ]);

    addAuditLog("AI Event", "ATS_ANALYSIS_RUN", `Executed ATS matching assessment. Output score: ${calculatedScore}%.`);
  };

  // Jobs
  const toggleSaveJob = (id: string) => {
    if (savedJobIds.includes(id)) {
      setSavedJobIds(savedJobIds.filter((item) => item !== id));
    } else {
      setSavedJobIds([...savedJobIds, id]);
    }
  };

  const searchJobs = (query: string, type: string): Job[] => {
    return jobs.filter((j) => {
      const matchQuery =
        j.title.toLowerCase().includes(query.toLowerCase()) ||
        j.company.toLowerCase().includes(query.toLowerCase()) ||
        j.skills_required.some((s) => s.toLowerCase().includes(query.toLowerCase()));
      const matchType = type === "" || j.type === type;
      return matchQuery && matchType;
    });
  };

  // AI Matcher
  const runAiMatcher = (jobId: string) => {
    const job = jobs.find((j) => j.id === jobId) || jobs[0];
    setUsage((prev) => ({ ...prev, job_matches: prev.job_matches + 1, ai_credits_used: prev.ai_credits_used + 100 }));

    const mockMatch: AIMatchReport = {
      job_id: job.id,
      match_score: 88,
      skill_gap: {
        matching: job.skills_required.slice(0, 3),
        missing: job.skills_required.slice(3)
      },
      salary_vs_market: "Highly competitive, aligns with top 10% percentile scales for similar locations.",
      custom_recommendations: [
        `Align resume experience bullets to explicitly showcase your success with ${job.skills_required[0]}.`,
        `Familiarize yourself with typical interview challenges regarding: ${job.requirements[0].substring(0, 30)}.`
      ]
    };
    setMatchReport(mockMatch);
    addAuditLog("AI Event", "AI_MATCHER_RUN", `Calculated match compatibility score of 88% against ${job.company}.`);
  };

  // Application tracker
  const moveApplicationStatus = (appId: string, status: any) => {
    const updated = applications.map((app) => {
      if (app.id === appId) {
        const timestamp = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
        return {
          ...app,
          status,
          timeline: [...app.timeline, { title: `Moved to ${status}`, date: timestamp, description: `Status update recorded manually.` }]
        };
      }
      return app;
    });
    setApplications(updated);
    addAuditLog("User Action", "MOVE_APPLICATION", `Updated application status to: ${status} for ID: ${appId}.`);
  };

  const addApplication = (jobId: string, jobTitle: string, company: string) => {
    const newApp: Application = {
      id: "app-" + Math.random().toString(36).substr(2, 9),
      job_id: jobId,
      job_title: jobTitle,
      company: company,
      status: "applied",
      applied_date: "Just now",
      notes: [],
      recruiters: [],
      timeline: [{ title: "Applied", date: "Just now", description: "Application registered." }]
    };
    setApplications([newApp, ...applications]);
    addAuditLog("User Action", "ADD_APPLICATION", `Registered pipeline track record for ${company} - ${jobTitle}.`);
  };

  const addRecruiterNote = (appId: string, note: string) => {
    setApplications(
      applications.map((app) => {
        if (app.id === appId) {
          return { ...app, notes: [...app.notes, note] };
        }
        return app;
      })
    );
  };

  // Mock Interview Platform
  const startMockInterview = (jobTitle: string, company: string, mode: "audio" | "text") => {
    setUsage((prev) => ({ ...prev, interview_sessions: prev.interview_sessions + 1, ai_credits_used: prev.ai_credits_used + 500 }));
    const session: InterviewSession = {
      id: "int-" + Math.random().toString(36).substr(2, 9),
      job_title: jobTitle,
      company: company,
      mode: mode,
      transcript: [
        {
          sender: "coach",
          text: `Welcome! Let's simulate a real-world panel for ${jobTitle} at ${company}. Can you summarize your most significant achievement scaling complex systems or architectures?`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        }
      ],
      created_at: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    };
    setActiveInterview(session);
    addAuditLog("AI Event", "START_INTERVIEW", `Launched mock interview framework for role: ${jobTitle} at ${company}.`);
  };

  const sendInterviewMessage = (text: string) => {
    if (!activeInterview) return;

    const candidateMsg = {
      sender: "candidate" as const,
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    // Simulate AI system dynamic coach answer
    setTimeout(() => {
      const coachMsg = {
        sender: "coach" as const,
        text: `That is a solid response. You explained the technical tradeoffs extremely well. Next, how do you handle collaborative deadlocks or alignment disputes inside cross-functional product pipelines?`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      setActiveInterview((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          transcript: [...prev.transcript, candidateMsg, coachMsg]
        };
      });
    }, 1000);

    setActiveInterview((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        transcript: [...prev.transcript, candidateMsg]
      };
    });
  };

  const completeInterview = () => {
    if (!activeInterview) return;

    const completed: InterviewSession = {
      ...activeInterview,
      score: 85,
      feedback: {
        clarity: 8.5,
        relevance: 9.0,
        depth: 8.0,
        general_remarks: "Polished and precise communication style. Confident technical execution.",
        actionable_points: [
          "Include slightly more details on metrics you delivered.",
          "Ensure answers structured using the STAR method are balanced between Situation and Action."
        ]
      }
    };

    setInterviews([completed, ...interviews]);
    setActiveInterview(null);
    addAuditLog("AI Event", "COMPLETE_INTERVIEW", `Compiled high-fidelity evaluation feedback matrix for ${completed.job_title}.`);
  };

  // Notifications
  const markNotificationsAsRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
  };

  const updateNotificationPreferences = (prefs: any) => {
    setNotificationPreferences({ ...notificationPreferences, ...prefs });
  };

  // Admin portal
  const updateAdminUserStatus = (userId: string, status: any) => {
    setAdminUsers(adminUsers.map((u) => (u.id === userId ? { ...u, status } : u)));
    addAuditLog("Admin Action", "UPDATE_USER_STATUS", `Admin modified account status of user ${userId} to ${status}.`);
  };

  const updateAdminUserRoles = (userId: string, roles: string[]) => {
    setAdminUsers(adminUsers.map((u) => (u.id === userId ? { ...u, roles } : u)));
    addAuditLog("Admin Action", "UPDATE_USER_ROLES", `Admin modified security claims of user ${userId} to ${roles.join(", ")}.`);
  };

  const updateSystemConfig = (key: string, value: any) => {
    setAdminConfigs(adminConfigs.map((c) => (c.config_key === key ? { ...c, config_value: value } : c)));
    addAuditLog("Admin Action", "UPDATE_SYSTEM_CONFIG", `Admin updated configuration parameter: ${key}.`);
  };

  const updateFeatureFlag = (id: string, updates: Partial<FeatureFlag>) => {
    setAdminFlags(adminFlags.map((f) => (f.id === id ? { ...f, ...updates } : f)));
    addAuditLog("Admin Action", "UPDATE_FEATURE_FLAG", `Admin changed status parameters of flag: ${id}.`);
  };

  const addAuditLog = (category: any, action: string, description: string) => {
    const newLog: AuditLog = {
      id: "log-" + Math.floor(1000 + Math.random() * 9000),
      user_id: user?.id,
      username: user?.username || "System",
      category,
      action,
      description,
      ip_address: "127.0.0.1",
      created_at: new Date().toISOString()
    };
    setAdminLogs((prev) => [newLog, ...prev]);
  };

  // Sync active plan object with code when subscription changes
  useEffect(() => {
    const matched = plans.find((p) => p.id === subscription.plan_id);
    if (matched) {
      setActivePlan(matched);
    }
  }, [subscription, plans]);

  return (
    <AppContext.Provider
      value={{
        user,
        mfaCodeNeeded,
        login,
        register,
        logout,
        verifyMfa,
        verifyEmailLink,
        resetPasswordRequest,
        currentTab,
        activeDashboardSubTab,
        setCurrentTab,
        setActiveDashboardSubTab,
        subscription,
        plans,
        usage,
        invoices,
        activePlan,
        upgradeSubscription,
        pauseSubscription,
        cancelSubscription,
        applyCouponCode,
        appliedDiscount,
        resumeVersions,
        selectedResumeVersion,
        templates: INITIAL_TEMPLATES,
        saveResumeVersion,
        addResumeVersion,
        setSelectedResumeVersion,
        atsReport,
        runAtsAnalysis,
        atsHistory,
        jobs,
        savedJobIds,
        toggleSaveJob,
        searchJobs,
        matchReport,
        runAiMatcher,
        applications,
        moveApplicationStatus,
        addApplication,
        addRecruiterNote,
        interviews,
        activeInterview,
        startMockInterview,
        sendInterviewMessage,
        completeInterview,
        notifications,
        markNotificationsAsRead,
        notificationPreferences,
        updateNotificationPreferences,
        adminUsers,
        adminConfigs,
        adminFlags,
        adminLogs,
        updateAdminUserStatus,
        updateAdminUserRoles,
        updateSystemConfig,
        updateFeatureFlag,
        addAuditLog
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppState = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppState must be handled inside an AppProvider context hierarchy.");
  }
  return context;
};
