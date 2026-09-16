import React, { useState } from "react";
import { useAppState } from "../store";
import { ResumeVersion } from "../types";
import {
  FileText,
  Plus,
  Save,
  Layers,
  Palette,
  Code,
  Download,
  UploadCloud,
  FileCheck,
  Sparkles,
  ListPlus
} from "lucide-react";

export default function ResumeModule() {
  const {
    resumeVersions,
    selectedResumeVersion,
    templates,
    saveResumeVersion,
    addResumeVersion,
    setSelectedResumeVersion
  } = useAppState();

  const [activeTemplate, setActiveTemplate] = useState(templates[0]);
  const [newVersionName, setNewVersionName] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  
  // Local state copy of current resume sections for edits
  const [personal, setPersonal] = useState(selectedResumeVersion?.sections.find(s => s.type === "personal")?.content || { name: "", email: "", phone: "", github: "" });
  const [summary, setSummary] = useState(selectedResumeVersion?.sections.find(s => s.type === "summary")?.content || "");
  const [skillsText, setSkillsText] = useState((selectedResumeVersion?.sections.find(s => s.type === "skills")?.content || []).join(", "));
  
  // Experience block edits
  const experienceSection = selectedResumeVersion?.sections.find(s => s.type === "experience");
  const initialExperience = experienceSection?.content || [{ role: "", company: "", duration: "", bullets: [] }];
  const [experiences, setExperiences] = useState<any[]>(initialExperience);

  // Synchronize when active version switches externally (e.g. on new version creation)
  React.useEffect(() => {
    if (selectedResumeVersion) {
      const pInfo = selectedResumeVersion.sections.find(s => s.type === "personal")?.content || { name: "", email: "", phone: "", github: "" };
      const summ = selectedResumeVersion.sections.find(s => s.type === "summary")?.content || "";
      const sk = (selectedResumeVersion.sections.find(s => s.type === "skills")?.content || []).join(", ");
      const exp = selectedResumeVersion.sections.find(s => s.type === "experience")?.content || [];
      
      setPersonal(pInfo);
      setSummary(summ);
      setSkillsText(sk);
      setExperiences(exp);
    }
  }, [selectedResumeVersion?.id]);

  // Synchronize when active version switches manually
  const handleVersionSwitch = (v: ResumeVersion) => {
    setSelectedResumeVersion(v);
  };

  const handleSave = () => {
    if (!selectedResumeVersion) return;

    const parsedSkills = skillsText.split(",").map(s => s.trim()).filter(Boolean);

    const updatedSections = [
      { id: "sec-p", type: "personal" as const, title: "Personal Information", content: personal },
      { id: "sec-s", type: "summary" as const, title: "Executive Summary", content: summary },
      { id: "sec-e", type: "experience" as const, title: "Professional Experience", content: experiences },
      { id: "sec-k", type: "skills" as const, title: "Technical Core Skills", content: parsedSkills }
    ];

    saveResumeVersion({
      ...selectedResumeVersion,
      sections: updatedSections
    });
  };

  const handleCreateVariant = (e: React.FormEvent) => {
    e.preventDefault();
    if (newVersionName.trim()) {
      addResumeVersion(newVersionName);
      setNewVersionName("");
    }
  };

  // Drag and drop simulator
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      triggerUpload();
    }
  };

  const triggerUpload = () => {
    setUploadSuccess(true);
    setTimeout(() => {
      setUploadSuccess(false);
      // Create a parsed document draft
      addResumeVersion("Parsed Resume Draft " + (resumeVersions.length + 1));
    }, 1500);
  };

  const addExperienceBlock = () => {
    setExperiences([...experiences, { role: "New Job Title", company: "Company Name", duration: "2026 - Present", bullets: ["Authored standard compliance microservices."] }]);
  };

  const updateExperienceField = (index: number, field: string, value: any) => {
    const updated = experiences.map((exp, idx) => {
      if (idx === index) {
        return { ...exp, [field]: value };
      }
      return exp;
    });
    setExperiences(updated);
  };

  const updateBulletPoint = (expIdx: number, bulletIdx: number, value: string) => {
    const updated = experiences.map((exp, idx) => {
      if (idx === expIdx) {
        const buls = [...exp.bullets];
        buls[bulletIdx] = value;
        return { ...exp, bullets: buls };
      }
      return exp;
    });
    setExperiences(updated);
  };

  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(selectedResumeVersion, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${selectedResumeVersion?.name || "resume"}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div id="resume-builder-module" className="space-y-6">
      
      {/* Selector and Uploader Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Version list picker */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
            <Layers className="h-4 w-4 text-emerald-400 mr-1" /> Active CV Sub-Drafts
          </h3>
          <div className="space-y-2 mb-4">
            {resumeVersions.map((v) => (
              <button
                key={v.id}
                onClick={() => handleVersionSwitch(v)}
                className={`w-full flex items-center justify-between p-3 rounded text-left transition-all border ${selectedResumeVersion?.id === v.id ? "bg-emerald-500/10 border-emerald-500 text-white" : "bg-slate-950 border-slate-850 text-slate-400 hover:text-slate-200"}`}
              >
                <div className="truncate pr-2">
                  <span className="block text-xs font-semibold">{v.name}</span>
                  <span className="text-[10px] text-slate-500 block">Edited: {v.updated_at}</span>
                </div>
                <FileCheck className={`h-4 w-4 shrink-0 ${selectedResumeVersion?.id === v.id ? "text-emerald-400" : "text-slate-600"}`} />
              </button>
            ))}
          </div>

          <form onSubmit={handleCreateVariant} className="flex space-x-2">
            <input
              type="text"
              required
              value={newVersionName}
              onChange={(e) => setNewVersionName(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
              placeholder="e.g. Frontend Sub-Variant"
            />
            <button type="submit" className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 p-1.5 rounded transition-colors shrink-0">
              <Plus className="h-4 w-4" />
            </button>
          </form>
        </div>

        {/* Drag-drop importer */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`bg-slate-900 border rounded-xl p-5 flex flex-col justify-between transition-all ${dragActive ? "border-emerald-500 bg-emerald-500/5" : "border-slate-800"}`}
        >
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1 flex items-center">
              <UploadCloud className="h-4 w-4 text-emerald-400 mr-1" /> PDF / DOCX Importer
            </h3>
            <p className="text-xs text-slate-500">Drag or click to simulate upload and parse with AI parser.</p>
          </div>

          <label
            htmlFor="resume-upload"
            className="border-2 border-dashed border-slate-800 hover:border-slate-700 bg-slate-950 rounded-lg p-6 text-center cursor-pointer my-4 flex flex-col items-center justify-center transition-colors"
          >
            <input 
              id="resume-upload"
              type="file" 
              className="hidden" 
              accept=".pdf,.docx,.doc" 
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  triggerUpload();
                  e.target.value = ''; // Reset
                }
              }} 
            />
            <UploadCloud className="h-8 w-8 text-slate-500 mb-2" />
            <span className="text-xs text-slate-300 block font-semibold">Drop or click here to upload</span>
            <span className="text-[10px] text-slate-500 block mt-1">PDF, DOCX formats supported</span>
          </label>

          {uploadSuccess && (
            <p className="text-[11px] text-emerald-400 text-center animate-pulse">
              ✔ Extracted raw layout details! Compiled new CV variant...
            </p>
          )}
        </div>

        {/* Template styling matrix */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center">
            <Palette className="h-4 w-4 text-emerald-400 mr-1" /> Template Style Matrix
          </h3>
          <div className="space-y-2">
            {templates.map((tpl) => (
              <button
                key={tpl.id}
                onClick={() => setActiveTemplate(tpl)}
                className={`w-full p-3 rounded text-left transition-all border ${activeTemplate.id === tpl.id ? "border-emerald-500 bg-slate-950" : "border-slate-850 bg-slate-950/40 hover:border-slate-850"}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white">{tpl.name}</span>
                  <span className="text-[9px] uppercase tracking-wider text-emerald-400 font-bold px-1.5 py-0.5 bg-emerald-500/10 rounded">
                    {tpl.category}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 leading-normal">{tpl.description}</p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Builder & Preview Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Editor Inputs Panel */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-5">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center">
              <Code className="h-4 w-4 text-emerald-400 mr-1" /> Sandbox Interactive Fields
            </h3>
            <button
              id="resume-save-btn"
              onClick={handleSave}
              className="px-3 py-1.5 bg-emerald-500 text-slate-950 rounded text-xs font-bold hover:bg-emerald-400 transition-colors inline-flex items-center"
            >
              <Save className="h-3.5 w-3.5 mr-1" /> Save Modifications
            </button>
          </div>

          {/* Form Personal Info */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Personal Details</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">Full Name</label>
                <input
                  type="text"
                  value={personal.name}
                  onChange={(e) => setPersonal({ ...personal, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">Email</label>
                <input
                  type="email"
                  value={personal.email}
                  onChange={(e) => setPersonal({ ...personal, email: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">Phone</label>
                <input
                  type="text"
                  value={personal.phone}
                  onChange={(e) => setPersonal({ ...personal, phone: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">GitHub / Portfolio</label>
                <input
                  type="text"
                  value={personal.github || ""}
                  onChange={(e) => setPersonal({ ...personal, github: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Executive Summary Statement</h4>
            <textarea
              rows={3}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
            />
          </div>

          {/* Core Skills */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Technical Core Skills</h4>
            <input
              type="text"
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
              placeholder="Comma separated lists, e.g. Python, React, JAX"
            />
          </div>

          {/* Experiences Block */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Professional Highlights</h4>
              <button
                onClick={addExperienceBlock}
                className="text-[10px] text-emerald-400 hover:underline flex items-center"
              >
                <ListPlus className="h-3 w-3 mr-1" /> Add Position
              </button>
            </div>

            <div className="space-y-4 max-h-64 overflow-y-auto pr-1">
              {experiences.map((exp: any, expIdx: number) => (
                <div key={expIdx} className="bg-slate-950 p-3 rounded border border-slate-850 space-y-2">
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-[9px] text-slate-500">Role Title</label>
                      <input
                        type="text"
                        value={exp.role}
                        onChange={(e) => updateExperienceField(expIdx, "role", e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[9px] text-slate-500">Company</label>
                      <input
                        type="text"
                        value={exp.company}
                        onChange={(e) => updateExperienceField(expIdx, "company", e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[9px] text-slate-500">Duration</label>
                      <input
                        type="text"
                        value={exp.duration}
                        onChange={(e) => updateExperienceField(expIdx, "duration", e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[9px] text-slate-500">Bullet Accomplishment</label>
                    {(exp.bullets || []).map((bullet: string, bulIdx: number) => (
                      <input
                        key={bulIdx}
                        type="text"
                        value={bullet}
                        onChange={(e) => updateBulletPoint(expIdx, bulIdx, e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-white mt-1"
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Live Preview Display Card */}
        <div className="bg-white text-slate-950 rounded-xl p-8 shadow-xl min-h-[500px] flex flex-col justify-between" style={{ fontFamily: activeTemplate.id === "tpl-3" ? "Georgia, serif" : "inherit" }}>
          <div>
            {/* Header style */}
            <div className="text-center border-b pb-4 mb-6" style={{ borderColor: activeTemplate.colors.secondary }}>
              <h2 className="text-2xl font-bold tracking-tight" style={{ color: activeTemplate.colors.primary }}>
                {personal.name || "Alex Catalyst"}
              </h2>
              <div className="text-xs text-slate-500 flex justify-center space-x-3 mt-1.5">
                <span>{personal.email || "alex@career.io"}</span>
                <span>•</span>
                <span>{personal.phone || "+1 555-0199"}</span>
                {personal.github && (
                  <>
                    <span>•</span>
                    <span>{personal.github}</span>
                  </>
                )}
              </div>
            </div>

            {/* Summary */}
            {summary && (
              <div className="mb-6">
                <h3 className="text-xs uppercase font-extrabold tracking-wider mb-2" style={{ color: activeTemplate.colors.primary }}>
                  Executive Summary
                </h3>
                <p className="text-xs leading-relaxed text-slate-700">{summary}</p>
              </div>
            )}

            {/* Core Skills section */}
            {skillsText && (
              <div className="mb-6">
                <h3 className="text-xs uppercase font-extrabold tracking-wider mb-2" style={{ color: activeTemplate.colors.primary }}>
                  Technical Skills
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {skillsText.split(",").map((sk, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] px-2.5 py-1 rounded-full border bg-slate-50 font-mono text-slate-700"
                    >
                      {sk.trim()}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Experience Block */}
            {experiences.length > 0 && (
              <div>
                <h3 className="text-xs uppercase font-extrabold tracking-wider mb-3" style={{ color: activeTemplate.colors.primary }}>
                  Professional Experience
                </h3>
                <div className="space-y-4">
                  {experiences.map((exp: any, idx: number) => (
                    <div key={idx} className="text-xs">
                      <div className="flex justify-between font-bold text-slate-900">
                        <span>{exp.role} — <span className="font-normal text-slate-600">{exp.company}</span></span>
                        <span className="font-mono text-slate-500">{exp.duration}</span>
                      </div>
                      <ul className="list-disc pl-4 mt-1.5 space-y-1 text-slate-700">
                        {(exp.bullets || []).map((bullet: string, bulIdx: number) => (
                          <li key={bulIdx}>{bullet}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Export action footer */}
          <div className="mt-8 border-t pt-4 flex justify-between text-xs text-slate-400 font-mono">
            <span>Template: {activeTemplate.name}</span>
            <div className="flex space-x-3">
              <button
                onClick={handleExportJSON}
                className="text-emerald-600 hover:text-emerald-700 hover:underline flex items-center font-bold"
              >
                <Code className="h-3.5 w-3.5 mr-1" /> Export JSON
              </button>
              <button
                onClick={() => alert("Simulated PDF compilation triggered! Standard LaTeX stylesheet rendered successfully.")}
                className="text-emerald-600 hover:text-emerald-700 hover:underline flex items-center font-bold"
              >
                <Download className="h-3.5 w-3.5 mr-1" /> Export LaTeX/PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
