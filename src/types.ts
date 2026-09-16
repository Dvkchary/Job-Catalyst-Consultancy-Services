import { ReactNode } from "react";

// ==========================================
// User & Authentication Types
// ==========================================
export interface UserProfile {
  id: string;
  username: string;
  email: string;
  status: "ACTIVE" | "PENDING" | "LOCKED" | "SUSPENDED";
  email_verified: boolean;
  mfa_enabled: boolean;
  roles: string[];
  last_login?: string;
  created_at: string;
}

// ==========================================
// Billing & Subscription Types
// ==========================================
export interface FeatureLimits {
  ai_credits: number;
  resume_limits: number;
  job_match_limits: number;
  interview_limits: number;
  storage_bytes: number;
  api_limits_per_min: number;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  code: "free" | "starter" | "professional" | "premium" | "enterprise";
  description: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  feature_limits: FeatureLimits;
  is_active: boolean;
  badge?: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan_id: string;
  status: "active" | "trialing" | "paused" | "canceled" | "expired";
  billing_period: "monthly" | "yearly";
  current_period_start: string;
  current_period_end: string;
  trial_start?: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
  payment_provider: "stripe" | "razorpay" | "paypal" | "custom";
}

export interface UsageMetric {
  ai_credits_used: number;
  resumes_parsed: number;
  ats_analyses: number;
  interview_sessions: number;
  job_matches: number;
  api_calls: number;
  storage_bytes: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  status: "paid" | "unpaid" | "refunded" | "open";
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  currency: string;
  billing_email: string;
  receipt_url?: string;
  created_at: string;
}

// ==========================================
// Resume Types
// ==========================================
export interface ResumeSection {
  id: string;
  type: "personal" | "experience" | "education" | "skills" | "summary" | "custom";
  title: string;
  content: any;
}

export interface ResumeVersion {
  id: string;
  name: string;
  updated_at: string;
  sections: ResumeSection[];
}

export interface ResumeTemplate {
  id: string;
  name: string;
  category: "Professional" | "Creative" | "Technical" | "Academic";
  is_published: boolean;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    text: string;
  };
}

// ==========================================
// ATS Analysis Types
// ==========================================
export interface ATSReport {
  score: number;
  keywords_found: string[];
  keywords_missing: string[];
  recommendations: string[];
  structural_feedback: {
    has_contact_info: boolean;
    has_summary: boolean;
    has_experience: boolean;
    has_education: boolean;
    has_skills: boolean;
    formatting_issues: string[];
  };
}

// ==========================================
// Job Searching & Matching Types
// ==========================================
export interface Job {
  id: string;
  title: string;
  company: string;
  logo?: string;
  location: string;
  type: "Full-Time" | "Part-Time" | "Contract" | "Remote" | "Hybrid";
  description: string;
  requirements: string[];
  skills_required: string[];
  salary_range: string;
  source: string;
  posted_at: string;
}

export interface AIMatchReport {
  job_id: string;
  match_score: number;
  skill_gap: {
    matching: string[];
    missing: string[];
  };
  salary_vs_market: string;
  custom_recommendations: string[];
}

// ==========================================
// Application Tracking Types
// ==========================================
export interface Application {
  id: string;
  job_id: string;
  job_title: string;
  company: string;
  status: "applied" | "screening" | "interviewing" | "offered" | "rejected";
  applied_date: string;
  notes: string[];
  recruiters: { name: string; contact?: string }[];
  timeline: { title: string; date: string; description?: string }[];
}

// ==========================================
// Interview Platform Types
// ==========================================
export interface InterviewSession {
  id: string;
  job_title: string;
  company: string;
  mode: "audio" | "text";
  transcript: { sender: "coach" | "candidate"; text: string; audio_url?: string; timestamp: string }[];
  score?: number;
  feedback?: {
    clarity: number;
    relevance: number;
    depth: number;
    general_remarks: string;
    actionable_points: string[];
  };
  created_at: string;
}

// ==========================================
// System Config & Admin Types
// ==========================================
export interface AuditLog {
  id: string;
  user_id?: string;
  username?: string;
  category: "Admin Action" | "User Action" | "AI Event" | "Security Event" | "System Event";
  action: string;
  description: string;
  ip_address?: string;
  created_at: string;
}

export interface FeatureFlag {
  id: string;
  name: string;
  description: string;
  is_enabled: boolean;
  rollout_percentage: number;
}

export interface SystemConfig {
  id: string;
  config_key: string;
  category: "Application" | "Email" | "Storage" | "Redis" | "Database" | "Environment";
  config_value: any;
  description: string;
}

// ==========================================
// Workflow Automation Types
// ==========================================
export interface Workflow {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  trigger_type: "MANUAL" | "SCHEDULED" | "EVENT_DRIVEN" | "API" | "WEBHOOK";
  trigger_config: Record<string, any>;
  definition: any;
  is_active: boolean;
  status: "DRAFT" | "ACTIVE" | "PAUSED";
  last_run_at?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  workflow?: Workflow;
  user_id: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED" | "PAUSED";
  trigger_source: string;
  current_step_index: number;
  context_data: Record<string, any>;
  steps_state: Record<string, {
    status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "RETRYING" | "PAUSED";
    output?: Record<string, any>;
    attempts?: number;
    error?: string;
    completed_at?: string;
  }>;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  trigger_type: string;
  trigger_config: Record<string, any>;
  definition: Record<string, any>;
  is_system: boolean;
}

export interface WorkflowLog {
  id: string;
  execution_id: string;
  step_name: string;
  level: "INFO" | "WARNING" | "ERROR" | "SUCCESS";
  message: string;
  timestamp: string;
}

// ==========================================
// AI Career OS Types (Module 1)
// ==========================================

export interface AICareerAssistantSession {
  id: string;
  title: string;
  context_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AICareerAssistantMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface CareerMemory {
  id: string;
  key: string;
  value: string;
  category: string;
  confidence: number;
  source?: string;
  created_at: string;
}

export interface CareerGoal {
  id: string;
  title: string;
  description?: string;
  target_date?: string;
  status: "pending" | "in_progress" | "achieved" | "abandoned";
  progress_percentage: number;
  milestones?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CareerHabit {
  id: string;
  title: string;
  frequency: string;
  streak: number;
  last_completed?: string;
  created_at: string;
}

export interface CareerTimelineEvent {
  id: string;
  event_date: string;
  title: string;
  description?: string;
  category: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface CareerDocument {
  id: string;
  name: string;
  document_type: string;
  file_url: string;
  size_bytes: number;
  created_at: string;
}

export interface AIWorkspaceProject {
  id: string;
  title: string;
  description?: string;
  workspace_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

