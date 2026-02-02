
import React, { useState, useEffect } from "react";
import { 
  Package, Upload, Download, Trash2, Search, Filter, 
  Archive, Box, Shield, Zap, CheckCircle, AlertTriangle 
} from "lucide-react";
import { pepAPI, teamAPI, rsbAPI, brcAPI } from "../lib/api";
import { toast } from "sonner";

// Simple UI Components
const Card = ({ children, className = "" }) => (
  <div className={`bg-card border border-border rounded-lg shadow-sm ${className}`}>
    {children}
  </div>
);

const Badge = ({ children, variant = "default" }) => {
  const variants = {
    default: "bg-primary/10 text-primary border-primary/20",
    success: "bg-green-500/10 text-green-500 border-green-500/20",
    warning: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    error: "bg-red-500/10 text-red-500 border-red-500/20",
  };
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full border ${variants[variant] || variants.default}`}>
      {children}
    </span>
  );
};

export default function PEPManager() {
  const [packs, setPacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Export/Import State
  const [showExportModal, setShowExportModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importStep, setImportStep] = useState("upload"); // upload, preview, importing
  const [previewData, setPreviewData] = useState(null);
  
  // Selection Data for Export
  const [teams, setTeams] = useState([]);
  const [rsbs, setRsbs] = useState([]);
  const [brcs, setBrcs] = useState([]);
  
  const [selectedTeams, setSelectedTeams] = useState([]);
  const [selectedRsbs, setSelectedRsbs] = useState([]);
  const [selectedBrcs, setSelectedBrcs] = useState([]);
  const [exportConfig, setExportConfig] = useState({
    env_tag: "sandbox",
    include_eval_suite: true,
    include_model_bundle: false
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await pepAPI.getAll();
      setPacks(res.data);
    } catch (err) {
      toast.error("Failed to load PEP packs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this pack?")) return;
    try {
      await pepAPI.delete(id);
      toast.success("Pack deleted");
      loadData();
    } catch (err) {
      toast.error("Failed to delete pack");
    }
  };

  const handleDownload = async (pack) => {
    // If we had a direct download URL, we'd use it. 
    // Usually stored files are served via static or presigned URL.
    // For now assuming storage path is local and maybe not directly exposed, 
    // or we might need a download endpoint. 
    // The current API doesn't have a direct download by ID for saved files, 
    // but the Export action returns a blob. 
    // We'll mark this as "Coming Soon" or implement a download route if needed.
    toast.info("Download from storage not yet implemented directly. Please export a new pack.");
  };

  // --- Export Logic ---
  const openExport = async () => {
    try {
      const [tRes, rRes, bRes] = await Promise.all([
        teamAPI.getAll(),
        rsbAPI.getAll(),
        brcAPI.getCatalog()
      ]);
      setTeams(tRes.data);
      setRsbs(rRes.data);
      setBrcs(bRes.data);
      setSelectedTeams([]);
      setSelectedRsbs([]);
      setSelectedBrcs([]);
      setShowExportModal(true);
    } catch (err) {
      toast.error("Failed to load data for export");
    }
  };

  const executeExport = async () => {
    if (selectedTeams.length === 0 && selectedRsbs.length === 0 && selectedBrcs.length === 0) {
      toast.error("Please select at least one item to export");
      return;
    }
    
    const toastId = toast.loading("Building PEP Pack...");
    try {
      const response = await pepAPI.export({
        team_ids: selectedTeams,
        rsb_ids: selectedRsbs,
        brc_ids: selectedBrcs,
        ...exportConfig
      });
      
      // Download blob
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const contentDisposition = response.headers['content-disposition'];
      const fileName = contentDisposition 
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `PEP_Export_${new Date().toISOString()}.zip`;
      
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("Export successful", { id: toastId });
      setShowExportModal(false);
      loadData(); // Refresh list to show newly saved export
    } catch (err) {
      toast.error("Export failed", { id: toastId });
      console.error(err);
    }
  };

  // --- Import Logic ---
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const toastId = toast.loading("Analyzing pack...");
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await pepAPI.preview(formData);
      setPreviewData(res.data);
      setImportStep("preview");
      // Store file for next step (in a real app, maybe upload to temp ID)
      // For now we will re-upload or keep in state if small? 
      // Actually we need to re-send the file for actual import.
      // We'll keep the file object in state.
      setPreviewData({...res.data, file}); 
      toast.dismiss(toastId);
    } catch (err) {
      toast.error("Invalid PEP file", { id: toastId });
    }
  };

  const executeImport = async () => {
    if (!previewData?.file) return;
    const toastId = toast.loading("Importing PEP...");
    const formData = new FormData();
    formData.append("file", previewData.file);
    
    try {
      await pepAPI.import(formData);
      toast.success("Import successful", { id: toastId });
      setShowImportModal(false);
      setPreviewData(null);
      setImportStep("upload");
      loadData();
    } catch (err) {
      toast.error("Import failed: " + err.response?.data?.detail, { id: toastId });
    }
  };

  const toggleSelection = (list, setList, id) => {
    setList(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const filteredPacks = packs.filter(p => 
    (p.id?.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (p.env_tag?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-2">
            <Package className="w-8 h-8 text-primary" />
            PEP Manager
          </h1>
          <p className="text-muted-foreground">
             Portable Evolution Packs - Transfer Intelligence between environments
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => { setShowImportModal(true); setImportStep("upload"); }} 
            className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 transition-colors"
          >
            <Upload className="w-4 h-4" /> Import Pack
          </button>
          <button 
            onClick={openExport}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Download className="w-4 h-4" /> Create Export
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Total Packs", value: packs.length, icon: Archive },
          { label: "Sandbox Packs", value: packs.filter(p => p.env_tag === 'sandbox').length, icon: Box },
          { label: "Production Packs", value: packs.filter(p => p.env_tag === 'production').length, icon: Shield },
          { label: "Imports", value: packs.filter(p => p.source === 'import').length, icon: Upload },
        ].map((stat, i) => (
          <Card key={i} className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
              <p className="text-2xl font-bold">{stat.value}</p>
            </div>
            <stat.icon className="w-8 h-8 text-muted-foreground/20" />
          </Card>
        ))}
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="p-4 border-b border-border flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input 
              type="text" 
              placeholder="Search packs..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <button className="p-2 text-muted-foreground hover:text-foreground">
            <Filter className="w-4 h-4" />
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Pack ID</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Environment</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Source</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Teams</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Contents</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredPacks.map(pack => (
                <tr key={pack.id} className="hover:bg-muted/10">
                  <td className="px-4 py-3 font-mono text-xs">{pack.id.substring(0, 12)}...</td>
                  <td className="px-4 py-3">{new Date(pack.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <Badge variant={pack.env_tag === 'production' ? 'error' : 'default'}>{pack.env_tag}</Badge>
                  </td>
                  <td className="px-4 py-3 capitalize">{pack.source || 'unknown'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {pack.teams?.slice(0, 2).map(t => (
                        <span key={t} className="text-xs bg-secondary px-1 rounded">{t}</span>
                      ))}
                      {pack.teams?.length > 2 && <span className="text-xs text-muted-foreground">+{pack.teams.length - 2}</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2 text-xs text-muted-foreground">
                      {pack.manifest?.rsb_count > 0 && <span title="RSBs">🛡️ {pack.manifest.rsb_count}</span>}
                      {pack.manifest?.brc_count > 0 && <span title="BRCs">⚔️ {pack.manifest.brc_count}</span>}
                      <span title="AMCs">🧠 {pack.manifest?.teams?.length || 0}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {/* <button onClick={() => handleDownload(pack)} className="text-blue-500 hover:text-blue-400">
                      <Download className="w-4 h-4" />
                    </button> */}
                    <button onClick={() => handleDelete(pack.id)} className="text-red-500 hover:text-red-400">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredPacks.length === 0 && (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-muted-foreground">No packs found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
      
      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card w-full max-w-2xl rounded-xl border border-border shadow-2xl flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-border">
              <h2 className="text-xl font-bold">Create Portable Evolution Pack</h2>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-1 block">Environment Tag</label>
                  <select 
                    value={exportConfig.env_tag}
                    onChange={e => setExportConfig({...exportConfig, env_tag: e.target.value})}
                    className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm"
                  >
                    <option value="sandbox">Sandbox</option>
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                  </select>
                </div>
                <div className="flex flex-col gap-2 mt-6">
                  <label className="flex items-center gap-2 text-sm">
                    <input 
                      type="checkbox" 
                      checked={exportConfig.include_eval_suite}
                      onChange={e => setExportConfig({...exportConfig, include_eval_suite: e.target.checked})}
                      className="rounded border-border bg-background"
                    />
                    Include Evaluation Suite
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input 
                      type="checkbox" 
                      checked={exportConfig.include_model_bundle}
                      onChange={e => setExportConfig({...exportConfig, include_model_bundle: e.target.checked})}
                      className="rounded border-border bg-background"
                    />
                    Include Model Weights (Large)
                  </label>
                </div>
              </div>
              
              {/* Selection Lists */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium mb-2 flex justify-between">
                    <span>Teams / Agents ({selectedTeams.length})</span>
                    <button onClick={() => setSelectedTeams(teams.map(t=>t.team_id))} className="text-xs text-primary">All</button>
                  </h3>
                  <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 border border-border rounded-md bg-muted/20">
                    {teams.map(t => (
                      <label key={t.team_id} className="flex items-center gap-2 text-sm p-1 hover:bg-muted/50 rounded cursor-pointer">
                        <input 
                          type="checkbox"
                          checked={selectedTeams.includes(t.team_id)}
                          onChange={() => toggleSelection(selectedTeams, setSelectedTeams, t.team_id)}
                        />
                        <span className="truncate">{t.bank_facing_name}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium mb-2 flex justify-between">
                    <span>Rule Suites (RSB) ({selectedRsbs.length})</span>
                    <button onClick={() => setSelectedRsbs(rsbs.map(r=>r.id))} className="text-xs text-primary">All</button>
                  </h3>
                  <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto p-2 border border-border rounded-md bg-muted/20">
                    {rsbs.map(r => (
                      <label key={r.id} className="flex items-center gap-2 text-sm p-1 hover:bg-muted/50 rounded cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={selectedRsbs.includes(r.id)}
                          onChange={() => toggleSelection(selectedRsbs, setSelectedRsbs, r.id)}
                        />
                        <span className="font-mono text-xs opacity-70 w-16">{r.version}</span>
                        <span className="truncate flex-1">{r.name}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium mb-2 flex justify-between">
                    <span>Battle Capsules (BRC) ({selectedBrcs.length})</span>
                    <button onClick={() => setSelectedBrcs(brcs.map(b=>b.id))} className="text-xs text-primary">All</button>
                  </h3>
                  <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto p-2 border border-border rounded-md bg-muted/20">
                    {brcs.map(b => (
                      <label key={b.id} className="flex items-center gap-2 text-sm p-1 hover:bg-muted/50 rounded cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={selectedBrcs.includes(b.id)}
                          onChange={() => toggleSelection(selectedBrcs, setSelectedBrcs, b.id)}
                        />
                        <span className="font-mono text-xs opacity-70 w-16">{b.battle_type}</span>
                        <span className="truncate flex-1">{new Date(b.created_at).toLocaleString()}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

            </div>
            
            <div className="p-6 border-t border-border flex justify-end gap-3">
              <button onClick={() => setShowExportModal(false)} className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors">Cancel</button>
              <button onClick={executeExport} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
                Export Pack
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card w-full max-w-lg rounded-xl border border-border shadow-2xl flex flex-col">
            <div className="p-6 border-b border-border">
              <h2 className="text-xl font-bold">Import PEP</h2>
            </div>
            
            <div className="p-6 space-y-6">
              {importStep === "upload" && (
                 <div className="border-2 border-dashed border-border rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-muted/20 hover:border-primary/50 transition-colors relative">
                    <input type="file" onChange={handleFileUpload} accept=".zip" className="absolute inset-0 opacity-0 cursor-pointer" />
                    <Upload className="w-12 h-12 text-muted-foreground mb-4" />
                    <h3 className="font-semibold text-lg">Drop PEP Zip File Here</h3>
                    <p className="text-sm text-muted-foreground mt-2">or click to browse</p>
                 </div>
              )}
              
              {importStep === "preview" && previewData && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-6 h-6 text-green-500" />
                    <div>
                      <h3 className="font-medium">File Validated</h3>
                      <p className="text-xs text-muted-foreground">ID: {previewData.manifest?.pack_id}</p>
                    </div>
                  </div>
                  
                  <div className="bg-muted/30 rounded-lg p-3 text-sm space-y-2">
                    <div className="flex justify-between">
                      <span>Environment:</span>
                      <span className="font-mono">{previewData.manifest?.env_tag}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Created:</span>
                      <span>{new Date(previewData.manifest?.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="border-t border-border/50 pt-2">
                      <p className="font-medium mb-1">Contents:</p>
                      <ul className="list-disc pl-4 text-muted-foreground">
                        <li>{previewData.capsules?.length || 0} Capsules</li>
                        {/* If preview returned checks for RSB/BRC inside we'd show them, 
                            currently pep_service.py preview just lists 'capsules' in zip. 
                            If we updated preview_pep_bytes to parse details we could show more. 
                            For now we trust the capsule list count.
                        */}
                        <li>Contracts & Manifest</li>
                      </ul>
                    </div>
                  </div>
                  
                  {previewData.manifest?.env_tag !== 'production' && (
                    <div className="flex items-start gap-2 text-yellow-500 bg-yellow-500/10 p-3 rounded-lg text-sm">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <p>This pack is from a <strong>{previewData.manifest?.env_tag}</strong> environment. Ensure compatibility before importing.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="p-6 border-t border-border flex justify-end gap-3">
              <button 
                onClick={() => { setShowImportModal(false); setPreviewData(null); }} 
                className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              {importStep === "preview" && (
                <button 
                  onClick={executeImport} 
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                  Confirm Import
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
