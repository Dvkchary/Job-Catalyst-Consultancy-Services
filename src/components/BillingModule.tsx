import React, { useState } from "react";
import { useAppState } from "../store";
import {
  Sparkles,
  CreditCard,
  FileText,
  Percent,
  Check,
  TrendingUp,
  Sliders,
  DollarSign,
  Download
} from "lucide-react";

export default function BillingModule() {
  const {
    plans,
    activePlan,
    usage,
    invoices,
    upgradeSubscription,
    pauseSubscription,
    cancelSubscription,
    applyCouponCode,
    appliedDiscount,
    subscription
  } = useAppState();

  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly");
  const [coupon, setCoupon] = useState("");
  const [couponSuccess, setCouponSuccess] = useState("");
  const [couponError, setCouponError] = useState("");

  const handleCouponSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCouponError("");
    setCouponSuccess("");

    if (coupon) {
      const res = applyCouponCode(coupon);
      if (res.success) {
        setCouponSuccess(res.message);
        setCoupon("");
      } else {
        setCouponError(res.message);
      }
    }
  };

  const calculateUsagePercent = (used: number, limit: number) => {
    return Math.min(100, Math.max(0, (used / limit) * 100));
  };

  return (
    <div id="billing-module" className="space-y-6 font-sans">
      
      {/* Plan selection matrix */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-850 pb-4 mb-6">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center">
              <CreditCard className="h-4 w-4 text-emerald-400 mr-1" /> Choose Subscription Plan
            </h3>
            <p className="text-xs text-slate-400 mt-1">Upgrade or modify your workspace plan limits securely.</p>
          </div>

          <div className="inline-flex items-center p-1 bg-slate-950 rounded-lg border border-slate-850 mt-3 md:mt-0">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={`px-3 py-1 text-xs font-semibold rounded transition-all ${billingPeriod === "monthly" ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white"}`}
            >
              Monthly Billing
            </button>
            <button
              onClick={() => setBillingPeriod("yearly")}
              className={`px-3 py-1 text-xs font-semibold rounded transition-all ${billingPeriod === "yearly" ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white"}`}
            >
              Yearly (Save 20%)
            </button>
          </div>
        </div>

        {/* 5-Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {plans.map((p) => {
            const isCurrent = p.id === activePlan.id;
            const price = billingPeriod === "monthly" ? p.price_monthly : p.price_yearly;
            const normalizedPrice = billingPeriod === "monthly" ? price : price / 12;

            return (
              <div
                key={p.id}
                className={`bg-slate-950 border rounded-xl p-5 flex flex-col justify-between hover:scale-[1.01] transition-all relative ${isCurrent ? "border-emerald-500" : "border-slate-850"}`}
              >
                {isCurrent && (
                  <span className="absolute -top-3 right-4 bg-emerald-500 text-slate-950 text-[10px] font-bold px-2 py-0.5 rounded-full">
                    Current Plan
                  </span>
                )}

                <div>
                  <h4 className="text-xs font-bold text-slate-100">{p.name}</h4>
                  <p className="text-[10px] text-slate-500 h-8 mt-1">{p.description}</p>
                  
                  <div className="flex items-baseline mt-3">
                    <span className="text-xl font-bold text-white">${normalizedPrice.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-500 ml-0.5">/mo</span>
                  </div>

                  <ul className="space-y-1.5 text-[10px] text-slate-400 mt-4 border-t border-slate-900 pt-3">
                    <li className="flex items-center">
                      <Check className="h-3 w-3 text-emerald-400 mr-1.5 shrink-0" />
                      <span>{p.feature_limits.ai_credits.toLocaleString()} Credits</span>
                    </li>
                    <li className="flex items-center">
                      <Check className="h-3 w-3 text-emerald-400 mr-1.5 shrink-0" />
                      <span>{p.feature_limits.resume_limits} Resumes</span>
                    </li>
                    <li className="flex items-center">
                      <Check className="h-3 w-3 text-emerald-400 mr-1.5 shrink-0" />
                      <span>{p.feature_limits.interview_limits} Mock Sessions</span>
                    </li>
                  </ul>
                </div>

                <button
                  id={`select-plan-${p.code}`}
                  onClick={() => upgradeSubscription(p.code, billingPeriod)}
                  className={`w-full mt-4 py-1.5 rounded text-xs font-bold transition-colors ${isCurrent ? "bg-emerald-500 text-slate-950 hover:bg-emerald-400" : "bg-slate-900 text-slate-350 hover:bg-slate-800"}`}
                >
                  {isCurrent ? "Active Plan" : "Choose Tier"}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Usage Metering sliders and Promo Code */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Sliders columns */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center mb-4">
            <Sliders className="h-4 w-4 text-emerald-400 mr-1" /> Dynamic Workspace Resource Metering
          </h3>

          <div className="space-y-4 text-xs">
            {/* AI Credits Meter */}
            <div>
              <div className="flex justify-between font-semibold mb-1">
                <span className="text-slate-300">AI Tokens Consumption</span>
                <span className="font-mono text-slate-400">
                  {usage.ai_credits_used.toLocaleString()} / {activePlan.feature_limits.ai_credits.toLocaleString()} Credits
                </span>
              </div>
              <div className="w-full bg-slate-950 h-2 rounded overflow-hidden border border-slate-850">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded transition-all"
                  style={{ width: `${calculateUsagePercent(usage.ai_credits_used, activePlan.feature_limits.ai_credits)}%` }}
                />
              </div>
            </div>

            {/* Resume Limits Meter */}
            <div>
              <div className="flex justify-between font-semibold mb-1">
                <span className="text-slate-300">Resume Formats Created</span>
                <span className="font-mono text-slate-400">
                  {usage.resumes_parsed} / {activePlan.feature_limits.resume_limits} CV versions
                </span>
              </div>
              <div className="w-full bg-slate-950 h-2 rounded overflow-hidden border border-slate-850">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded transition-all"
                  style={{ width: `${calculateUsagePercent(usage.resumes_parsed, activePlan.feature_limits.resume_limits)}%` }}
                />
              </div>
            </div>

            {/* Interview Sessions Meter */}
            <div>
              <div className="flex justify-between font-semibold mb-1">
                <span className="text-slate-300">Mock Interview Coach Practice</span>
                <span className="font-mono text-slate-400">
                  {usage.interview_sessions} / {activePlan.feature_limits.interview_limits} sessions
                </span>
              </div>
              <div className="w-full bg-slate-950 h-2 rounded overflow-hidden border border-slate-850">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded transition-all"
                  style={{ width: `${calculateUsagePercent(usage.interview_sessions, activePlan.feature_limits.interview_limits)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Coupon promos box */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2 flex items-center">
              <Percent className="h-4 w-4 text-emerald-400 mr-1" /> Redeem Promotion Coupons
            </h3>
            <p className="text-xs text-slate-500 mb-4">Enter promotional credit keys or referral triggers.</p>

            <form onSubmit={handleCouponSubmit} className="space-y-3">
              <input
                type="text"
                required
                value={coupon}
                onChange={(e) => setCoupon(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white uppercase font-mono tracking-wider focus:outline-none focus:border-emerald-500"
                placeholder="e.g. DISCOUNT20"
              />
              <button type="submit" className="w-full py-1.5 bg-emerald-500 text-slate-950 rounded text-xs font-bold hover:bg-emerald-400 transition-colors">
                Apply Code
              </button>
            </form>

            {couponSuccess && <p className="text-[11px] text-emerald-400 mt-2 font-mono animate-pulse">{couponSuccess}</p>}
            {couponError && <p className="text-[11px] text-red-400 mt-2 font-mono">{couponError}</p>}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-850 text-[10px] text-slate-500 leading-normal">
            Hint: Use promo <span className="text-emerald-400 font-bold font-mono">DISCOUNT20</span> (for 20% off) or <span className="text-emerald-400 font-bold font-mono">FREEPROMO</span> (100% free credits) inside development profiles.
          </div>
        </div>
      </div>

      {/* Invoice list */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
          <FileText className="h-4 w-4 text-emerald-400 mr-1" /> Paid Receipts & Invoices
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 border-b border-slate-850 uppercase font-bold tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3">Invoice ID</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Subtotal</th>
                <th className="px-4 py-3">Tax</th>
                <th className="px-4 py-3">Discounts</th>
                <th className="px-4 py-3">Total paid</th>
                <th className="px-4 py-3 text-right">Receipt File</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850">
              {invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-slate-950/40">
                  <td className="px-4 py-3 font-semibold text-white">{inv.invoice_number}</td>
                  <td className="px-4 py-3 text-slate-450">{new Date(inv.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 font-mono">${inv.subtotal.toFixed(2)}</td>
                  <td className="px-4 py-3 font-mono">${inv.tax.toFixed(2)}</td>
                  <td className="px-4 py-3 font-mono text-emerald-400">-${inv.discount.toFixed(2)}</td>
                  <td className="px-4 py-3 font-mono text-white font-bold">${inv.total.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => alert(`Downloading invoice statement ${inv.invoice_number} PDF...`)}
                      className="text-emerald-400 hover:text-emerald-300 hover:underline inline-flex items-center font-bold"
                    >
                      <Download className="h-3 w-3 mr-1" /> PDF Receipt
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
