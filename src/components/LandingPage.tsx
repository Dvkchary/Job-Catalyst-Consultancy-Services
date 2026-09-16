import React, { useState } from "react";
import { useAppState } from "../store";
import {
  Sparkles,
  Zap,
  ShieldCheck,
  ArrowRight,
  TrendingUp,
  Cpu,
  Mail,
  HelpCircle,
  FileText,
  UserCheck,
  ChevronRight,
  Check
} from "lucide-react";

export default function LandingPage() {
  const { setCurrentTab, plans, upgradeSubscription } = useAppState();
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactMsg, setContactMsg] = useState("");
  const [contactSuccess, setContactSuccess] = useState(false);

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (contactEmail) {
      setContactSuccess(true);
      setTimeout(() => setContactSuccess(false), 5000);
      setContactName("");
      setContactEmail("");
      setContactMsg("");
    }
  };

  const faqs = [
    { q: "How does the AI Resume parsing engine score my format?", a: "JobCatalyst leverages deep parsing graphs to replicate standard ATS parser engines. It flags unrecognized custom symbols, column overflows, and quantifies keyword density." },
    { q: "Can I upgrade, downgrade, or cancel at any time?", a: "Absolutely. Our billing system supports prorated Stripe transfers. When canceling, your pro features will remain active until the period terminates." },
    { q: "What models power the Mock Interview coach?", a: "We route prompts through our central AI Gateway using Gemini Flash models optimized with specialized prompt instructions for real-time career coaching." }
  ];

  const blogPosts = [
    { title: "Sailing through ATS Parsers in 2026", desc: "Why columns and custom symbols can filter out top engineers, and how to structure plain text resumes.", date: "July 1, 2026" },
    { title: "Mastering the STAR framework for AI Panelists", desc: "Tips on structuring metrics-driven achievements when conversing with real-time audio mock interviewers.", date: "June 28, 2026" }
  ];

  return (
    <div id="landing-page" className="min-h-screen bg-slate-950 text-slate-100 selection:bg-emerald-500 selection:text-slate-900 font-sans">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="bg-emerald-500 text-slate-950 p-1.5 rounded font-mono font-bold tracking-tighter text-lg">
              JC
            </div>
            <span className="font-sans font-bold tracking-tight text-lg text-white">
              JobCatalyst <span className="text-emerald-400">AI</span>
            </span>
          </div>
          <nav className="hidden md:flex space-x-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-emerald-400 transition-colors">Features</a>
            <a href="#pricing" className="hover:text-emerald-400 transition-colors">Pricing</a>
            <a href="#blog" className="hover:text-emerald-400 transition-colors">Blog</a>
            <a href="#docs" className="hover:text-emerald-400 transition-colors">Docs</a>
            <a href="#contact" className="hover:text-emerald-400 transition-colors">Contact</a>
          </nav>
          <div className="flex items-center space-x-3">
            <button
              id="landing-login-btn"
              onClick={() => setCurrentTab("auth")}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              Log In
            </button>
            <button
              id="landing-signup-btn"
              onClick={() => setCurrentTab("auth")}
              className="px-4 py-2 text-sm font-medium bg-emerald-500 text-slate-950 rounded hover:bg-emerald-400 transition-all font-semibold shadow-lg shadow-emerald-500/20"
            >
              Get Started Free
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-24 sm:py-32 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(16,185,129,0.08),transparent_50%)]" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="max-w-3xl">
            <div className="inline-flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-full px-3 py-1 text-xs text-emerald-400 mb-6">
              <Sparkles className="h-3 w-3" />
              <span>Next-Gen Enterprise Job Search & Resume Intelligence</span>
            </div>
            <h1 className="text-5xl sm:text-6xl font-bold tracking-tight text-white mb-6">
              Catalyze your career path with <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">Enterprise AI</span>
            </h1>
            <p className="text-lg text-slate-400 leading-relaxed mb-8">
              Build compliant resumes, optimize formatting through ATS sandbox simulations, match matching scores, coordinate applications pipelines, and mock speech panels in real-time.
            </p>
            <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
              <button
                id="hero-get-started"
                onClick={() => setCurrentTab("auth")}
                className="flex items-center justify-center px-6 py-3 bg-emerald-500 text-slate-950 font-semibold rounded hover:bg-emerald-400 transition-all shadow-lg shadow-emerald-500/10 group"
              >
                <span>Launch Interactive Sandbox</span>
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </button>
              <a
                href="#pricing"
                className="flex items-center justify-center px-6 py-3 border border-slate-800 bg-slate-900/50 rounded font-medium text-slate-300 hover:text-white hover:border-slate-700 transition-colors"
              >
                Compare Enterprise Plans
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 border-t border-slate-900 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Engineered with Enterprise-Grade Precision
            </h2>
            <p className="mt-4 text-slate-400">
              A comprehensive system utilizing unified RBAC security, dynamic Gemini LLM gateway routers, and persistent transactional databases.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-slate-900/50 border border-slate-900 p-8 rounded-xl hover:border-emerald-500/20 transition-all">
              <div className="bg-emerald-500/10 p-3 rounded-lg w-fit text-emerald-400 mb-6">
                <FileText className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Modular Resume Compiler</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Dynamic LaTeX and JSON resume builders optimized for standard plain text schema indices. Compile and track custom sub-variants.
              </p>
            </div>

            <div className="bg-slate-900/50 border border-slate-900 p-8 rounded-xl hover:border-emerald-500/20 transition-all">
              <div className="bg-emerald-500/10 p-3 rounded-lg w-fit text-emerald-400 mb-6">
                <TrendingUp className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">ATS Sandbox Simulation</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Analyze document compliance structure, identify missing technical skill keywords, and preview formatting compliance immediately.
              </p>
            </div>

            <div className="bg-slate-900/50 border border-slate-900 p-8 rounded-xl hover:border-emerald-500/20 transition-all">
              <div className="bg-emerald-500/10 p-3 rounded-lg w-fit text-emerald-400 mb-6">
                <Cpu className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Mock Panel Coach</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Real-time conversational evaluation interface analyzing speech density, keyword relevance, and STAR layout structures.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 border-t border-slate-900 bg-slate-950/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Flexible, Compliant Pricing
            </h2>
            <p className="mt-4 text-slate-400">
              Pick the tier that fits your pacing. Custom configurations available for enterprises.
            </p>
            <div className="mt-8 inline-flex items-center p-1 bg-slate-900 rounded-lg border border-slate-800">
              <button
                onClick={() => setBillingPeriod("monthly")}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${billingPeriod === "monthly" ? "bg-emerald-500 text-slate-950 shadow" : "text-slate-400 hover:text-white"}`}
              >
                Monthly Billing
              </button>
              <button
                onClick={() => setBillingPeriod("yearly")}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${billingPeriod === "yearly" ? "bg-emerald-500 text-slate-950 shadow" : "text-slate-400 hover:text-white"}`}
              >
                Yearly (Save 20%)
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {plans.map((p) => {
              const basePrice = billingPeriod === "monthly" ? p.price_monthly : p.price_yearly;
              const normalizedPrice = billingPeriod === "monthly" ? basePrice : basePrice / 12;
              return (
                <div
                  key={p.id}
                  className={`bg-slate-900 border rounded-xl p-6 flex flex-col justify-between hover:scale-[1.01] transition-all relative ${p.badge ? "border-emerald-500/50 shadow-md shadow-emerald-500/5" : "border-slate-800"}`}
                >
                  {p.badge && (
                    <span className="absolute -top-3 right-4 bg-emerald-500 text-slate-950 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {p.badge}
                    </span>
                  )}
                  <div>
                    <h3 className="text-md font-bold text-white mb-1">{p.name}</h3>
                    <p className="text-xs text-slate-400 h-10 mb-4">{p.description}</p>
                    <div className="flex items-baseline mb-4">
                      <span className="text-3xl font-bold text-white">${normalizedPrice.toFixed(2)}</span>
                      <span className="text-xs text-slate-500 ml-1">/mo</span>
                    </div>
                    <ul className="space-y-2 text-xs text-slate-300 mb-6 border-t border-slate-800 pt-4">
                      <li className="flex items-center">
                        <Check className="h-3 w-3 text-emerald-400 mr-2" />
                        <span>{p.feature_limits.ai_credits} AI Credits</span>
                      </li>
                      <li className="flex items-center">
                        <Check className="h-3 w-3 text-emerald-400 mr-2" />
                        <span>{p.feature_limits.resume_limits} Resume Drafts</span>
                      </li>
                      <li className="flex items-center">
                        <Check className="h-3 w-3 text-emerald-400 mr-2" />
                        <span>{p.feature_limits.interview_limits} Interview Sessions</span>
                      </li>
                      <li className="flex items-center">
                        <Check className="h-3 w-3 text-emerald-400 mr-2" />
                        <span>{p.feature_limits.job_match_limits} Match Audits</span>
                      </li>
                    </ul>
                  </div>
                  <button
                    onClick={() => {
                      setCurrentTab("auth");
                    }}
                    className={`w-full py-2 rounded text-xs font-semibold text-center transition-all ${p.badge ? "bg-emerald-500 text-slate-950 hover:bg-emerald-400" : "bg-slate-800 text-slate-200 hover:bg-slate-700"}`}
                  >
                    Select Plan
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Blog & Docs section */}
      <section id="blog" className="py-20 border-t border-slate-900 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Blog */}
            <div>
              <h3 className="text-2xl font-bold text-white mb-6 flex items-center">
                <FileText className="h-5 w-5 text-emerald-400 mr-2" />
                Latest Developer Publications
              </h3>
              <div className="space-y-6">
                {blogPosts.map((post, i) => (
                  <div key={i} className="bg-slate-900/40 border border-slate-900 p-6 rounded-lg">
                    <span className="text-xs text-emerald-400">{post.date}</span>
                    <h4 className="text-lg font-semibold text-white mt-2 mb-2">{post.title}</h4>
                    <p className="text-sm text-slate-400 mb-4">{post.desc}</p>
                    <button onClick={() => setCurrentTab("auth")} className="text-xs text-emerald-400 hover:underline inline-flex items-center font-medium">
                      Read publication <ChevronRight className="h-3 w-3 ml-1" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Docs */}
            <div id="docs">
              <h3 className="text-2xl font-bold text-white mb-6 flex items-center">
                <ShieldCheck className="h-5 w-5 text-emerald-400 mr-2" />
                API & Architecture Documentation
              </h3>
              <div className="bg-slate-900/40 border border-slate-900 p-6 rounded-lg space-y-4">
                <div className="border-b border-slate-800 pb-4">
                  <h4 className="text-sm font-semibold text-white">/api/v1/billing/subscribe</h4>
                  <p className="text-xs text-slate-400 mt-1">Registers subscription changes. Maps Stripe and Razorpay checkout parameters with direct database synchronization.</p>
                </div>
                <div className="border-b border-slate-800 pb-4">
                  <h4 className="text-sm font-semibold text-white">/api/v1/ats/analyze</h4>
                  <p className="text-xs text-slate-400 mt-1">Routes text blobs through our LLM parsing agent. Quantifies score and recommends missing skill keywords.</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">/api/v1/interviews/session</h4>
                  <p className="text-xs text-slate-400 mt-1">Starts real-time state machine tracking question cycles and logs answers for structured feedback compilation.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 border-t border-slate-900 bg-slate-950/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <h3 className="text-3xl font-bold text-white mb-12 text-center flex items-center justify-center">
            <HelpCircle className="h-6 w-6 text-emerald-400 mr-2" /> Frequently Asked Questions
          </h3>
          <div className="space-y-6">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-slate-900 border border-slate-800 p-6 rounded-lg">
                <h4 className="text-md font-semibold text-white mb-2">{faq.q}</h4>
                <p className="text-sm text-slate-400 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-20 border-t border-slate-900 bg-slate-950">
        <div className="max-w-lg mx-auto px-4">
          <div className="text-center mb-8">
            <Mail className="h-8 w-8 text-emerald-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-white">Get in touch with an Expert</h3>
            <p className="text-sm text-slate-400 mt-2">Need a custom enterprise SLA or team quota limits? Drop us a line.</p>
          </div>
          <form onSubmit={handleContactSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="Alex Mercer"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="alex@enterprise.com"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Message Description</label>
              <textarea
                rows={4}
                required
                value={contactMsg}
                onChange={(e) => setContactMsg(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="Describe your user volume or pricing inquiries..."
              />
            </div>
            <button
              id="landing-submit-contact"
              type="submit"
              className="w-full py-2.5 bg-emerald-500 text-slate-950 font-semibold rounded hover:bg-emerald-400 transition-colors text-sm"
            >
              Submit Contact Request
            </button>
            {contactSuccess && (
              <p className="text-xs text-emerald-400 text-center mt-2 animate-pulse">
                Successfully captured submission! An integration expert will follow up within 4 hours.
              </p>
            )}
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-slate-950 border-t border-slate-900 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between">
          <p>© 2026 JobCatalyst AI Inc. All rights reserved.</p>
          <div className="flex space-x-6 mt-4 sm:mt-0">
            <a href="#landing-page" className="hover:text-slate-300">Privacy Policy</a>
            <a href="#landing-page" className="hover:text-slate-300">Terms of Service</a>
            <a href="#docs" className="hover:text-slate-300">Security Architecture</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
