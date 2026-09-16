import React, { useState } from "react";
import { useAppState } from "../store";
import { Shield, Key, Mail, User, CheckCircle, RefreshCw, Smartphone } from "lucide-react";

export default function AuthScreen() {
  const { login, register, verifyMfa, verifyEmailLink, resetPasswordRequest, setCurrentTab } = useAppState();

  const [mode, setMode] = useState<"login" | "register" | "forgot" | "mfa">("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  
  const [infoMsg, setInfoMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isVerifyingLink, setIsVerifyingLink] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setInfoMsg("");

    try {
      if (mode === "login") {
        const success = await login(email, password);
        if (success) {
          // If the user email matches the seed admin/test we skip MFA or can configure it
          if (email === "6309vs@gmail.com") {
            setMode("mfa");
            setInfoMsg("MFA code required for administrative account. Use verification code '123456'.");
          } else {
            setCurrentTab("dashboard");
          }
        } else {
          setErrorMsg("Invalid username, email, or credentials.");
        }
      } else if (mode === "register") {
        if (!username || !email || !password) {
          setErrorMsg("All fields are strictly required.");
          return;
        }
        await register(username, email, password);
        setInfoMsg("Registration parsed! Verification email routed. Confirm verification link below to continue.");
      } else if (mode === "forgot") {
        resetPasswordRequest(email);
        setInfoMsg(`Recovery link compiled and routed to ${email}. Check your sandbox inbox.`);
      } else if (mode === "mfa") {
        const correct = verifyMfa(mfaCode);
        if (correct) {
          setCurrentTab("dashboard");
        } else {
          setErrorMsg("Invalid security authorization code. Use '123456'.");
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || "An authentication error occurred.");
    }
  };

  const handleSimulatedVerification = () => {
    setIsVerifyingLink(true);
    setTimeout(() => {
      verifyEmailLink();
      setIsVerifyingLink(false);
      setInfoMsg("Email confirmed successfully! You can now log into your sandbox profile.");
      setMode("login");
    }, 1500);
  };

  return (
    <div id="auth-screen" className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(16,185,129,0.05),transparent_40%)]" />
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-8 relative shadow-2xl">
        
        {/* Branding */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-emerald-500 text-slate-950 p-2.5 rounded-lg font-mono font-bold tracking-tighter text-xl mb-3 shadow-lg shadow-emerald-500/20">
            JC
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            {mode === "login" && "Welcome Back"}
            {mode === "register" && "Create Developer Account"}
            {mode === "forgot" && "Recover Security Credentials"}
            {mode === "mfa" && "Multi-Factor Authentication"}
          </h2>
          <p className="text-xs text-slate-400 mt-1 text-center">
            {mode === "login" && "Access your JobCatalyst analytical workspaces."}
            {mode === "register" && "Start formatting compliant resumes today."}
            {mode === "forgot" && "Reset your password securely."}
            {mode === "mfa" && "Enterprise policy requires a second factor verification."}
          </p>
        </div>

        {/* Info or Error Alerts */}
        {errorMsg && (
          <div className="bg-red-950/40 border border-red-900 text-red-400 text-xs p-3 rounded mb-4">
            {errorMsg}
          </div>
        )}
        {infoMsg && (
          <div className="bg-emerald-950/40 border border-emerald-900 text-emerald-400 text-xs p-3 rounded mb-4">
            {infoMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1 flex items-center">
                <User className="h-3.5 w-3.5 mr-1 text-emerald-400" /> Username
              </label>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="developer_catalyst"
              />
            </div>
          )}

          {mode !== "mfa" && (
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1 flex items-center">
                <Mail className="h-3.5 w-3.5 mr-1 text-emerald-400" /> Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="6309vs@gmail.com"
              />
            </div>
          )}

          {(mode === "login" || mode === "register") && (
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1 flex items-center">
                <Key className="h-3.5 w-3.5 mr-1 text-emerald-400" /> Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="••••••••"
              />
            </div>
          )}

          {mode === "mfa" && (
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1 flex items-center">
                <Smartphone className="h-3.5 w-3.5 mr-1 text-emerald-400" /> Six-Digit Token
              </label>
              <input
                type="text"
                required
                maxLength={6}
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-center font-mono tracking-widest text-white focus:outline-none focus:border-emerald-500"
                placeholder="123456"
              />
            </div>
          )}

          <button
            id="auth-submit-btn"
            type="submit"
            className="w-full py-2 bg-emerald-500 text-slate-950 font-bold rounded hover:bg-emerald-400 transition-colors text-sm shadow-md"
          >
            {mode === "login" && "Authenticate Session"}
            {mode === "register" && "Register Account"}
            {mode === "forgot" && "Route Recovery Request"}
            {mode === "mfa" && "Authorize Identity"}
          </button>
        </form>

        {/* Simulated helper tools to mimic backend emails */}
        {mode === "register" && (
          <div className="mt-6 pt-6 border-t border-slate-800 text-center">
            <p className="text-[11px] text-slate-500 mb-2">Simulate instant email verification loop (Developer Sandbox):</p>
            <button
              id="simulate-verify-btn"
              onClick={handleSimulatedVerification}
              disabled={isVerifyingLink}
              className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded text-xs hover:bg-emerald-500/20 transition-all inline-flex items-center space-x-1"
            >
              {isVerifyingLink ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" />
                  <span>Verifying Link...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-3.5 w-3.5 mr-1" />
                  <span>Click to Verification Simulation Link</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Mode Toggles */}
        <div className="mt-6 flex flex-col space-y-2 text-center text-xs text-slate-400">
          {mode === "login" && (
            <>
              <button onClick={() => setMode("register")} className="hover:text-emerald-400 transition-colors">
                New to JobCatalyst? <span className="text-emerald-400 font-semibold underline">Create account</span>
              </button>
              <button onClick={() => setMode("forgot")} className="hover:text-emerald-400 transition-colors">
                Forgot your password credentials?
              </button>
            </>
          )}

          {mode === "register" && (
            <button onClick={() => setMode("login")} className="hover:text-emerald-400 transition-colors">
              Already have an account? <span className="text-emerald-400 font-semibold underline">Sign In</span>
            </button>
          )}

          {mode === "forgot" && (
            <button onClick={() => setMode("login")} className="hover:text-emerald-400 transition-colors">
              Return to <span className="text-emerald-400 font-semibold underline">Sign In</span>
            </button>
          )}

          {mode === "mfa" && (
            <button
              onClick={() => {
                setMode("login");
                setErrorMsg("");
                setInfoMsg("");
              }}
              className="hover:text-emerald-400 transition-colors"
            >
              Sign in with a different user profile
            </button>
          )}

          <button onClick={() => setCurrentTab("landing")} className="text-slate-500 hover:text-slate-300 transition-colors pt-2">
            ← Back to Landing Page
          </button>
        </div>
      </div>
    </div>
  );
}
