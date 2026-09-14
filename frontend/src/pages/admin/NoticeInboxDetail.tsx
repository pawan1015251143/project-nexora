import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Loader2, AlertCircle, CheckCircle, XCircle,
  Sparkles, Eye, FileText, MessageSquare, Clock, Send, Edit3, RotateCcw
} from "lucide-react";
import { API_URL } from "../../config";

// ── Types ─────────────────────────────────────────────────────────────────────

interface DemoSourceMessage {
  id: number;
  source_message_id: string;
  group_name: string;
  sender: string;
  message_text: string;
  attachment_name?: string;
  attachment_type?: string;
  attachment_content?: string;
  timestamp: string;
  imported: boolean;
  content_hash: string;
}

interface NoticeImportRecord {
  id: number;
  status: string;
  draft_title?: string;
  draft_content?: string;
  draft_notice_type?: string;
  ai_extracted_json?: Record<string, any>;
  processing_error?: string;
  imported_at?: string;
  processed_at?: string;
  approved_at?: string;
  rejected_at?: string;
  published_at?: string;
  notice_id?: number;
}

interface InboxItem {
  source: DemoSourceMessage;
  import_record?: NoticeImportRecord;
}

// ── Status badge ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  new: { label: "New", color: "bg-sky-100 text-sky-800 border-sky-200", icon: <Clock className="h-3 w-3" /> },
  imported: { label: "Imported", color: "bg-blue-100 text-blue-800 border-blue-200", icon: <Clock className="h-3 w-3" /> },
  processing: { label: "Processing", color: "bg-yellow-100 text-yellow-800 border-yellow-200", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  draft: { label: "Draft Ready", color: "bg-purple-100 text-purple-800 border-purple-200", icon: <Edit3 className="h-3 w-3" /> },
  pending_approval: { label: "Pending Approval", color: "bg-orange-100 text-orange-800 border-orange-200", icon: <Clock className="h-3 w-3" /> },
  approved: { label: "Approved", color: "bg-emerald-100 text-emerald-800 border-emerald-200", icon: <CheckCircle className="h-3 w-3" /> },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800 border-red-200", icon: <XCircle className="h-3 w-3" /> },
  published: { label: "Published ✓", color: "bg-green-100 text-green-800 border-green-200", icon: <CheckCircle className="h-3 w-3" /> },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: "bg-gray-100 text-gray-700 border-gray-200", icon: null };
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.color}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ── Pipeline steps indicator ──────────────────────────────────────────────────

const STEPS = [
  { key: ["new"], label: "Received" },
  { key: ["imported"], label: "Imported" },
  { key: ["processing", "draft"], label: "AI Processed" },
  { key: ["pending_approval", "approved"], label: "Approved" },
  { key: ["published"], label: "Published" },
];

function PipelineIndicator({ status }: { status: string }) {
  const getStep = () => {
    if (status === "rejected") return -1;
    for (let i = 0; i < STEPS.length; i++) {
      if (STEPS[i].key.includes(status)) return i;
    }
    return 0;
  };
  const currentStep = getStep();
  const isRejected = status === "rejected";

  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step, idx) => {
        const done = !isRejected && idx <= currentStep;
        const active = !isRejected && idx === currentStep;
        return (
          <React.Fragment key={step.label}>
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                done ? "bg-indigo-600 border-indigo-600 text-white" : "bg-white border-gray-300 text-gray-400"
              } ${active ? "ring-2 ring-indigo-300 ring-offset-2" : ""}`}>
                {idx + 1}
              </div>
              <span className={`text-xs mt-1 font-medium ${done ? "text-indigo-600" : "text-gray-400"}`}>
                {step.label}
              </span>
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`h-0.5 w-12 -mt-4 mb-4 transition-all ${
                !isRejected && idx < currentStep ? "bg-indigo-600" : "bg-gray-200"
              }`} />
            )}
          </React.Fragment>
        );
      })}
      {isRejected && (
        <div className="ml-4 flex items-center gap-1 text-red-600 text-sm font-medium">
          <XCircle className="h-4 w-4" />
          Rejected
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function NoticeInboxDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");

  const [item, setItem] = useState<InboxItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  // Editable draft fields
  const [draftTitle, setDraftTitle] = useState("");
  const [draftContent, setDraftContent] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);

  const showToast = (msg: string, type: "success" | "error") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const fetchItem = async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/notice-inbox/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load notice");
      const data: InboxItem = await res.json();
      setItem(data);
      if (data.import_record?.draft_title) setDraftTitle(data.import_record.draft_title);
      if (data.import_record?.draft_content) setDraftContent(data.import_record.draft_content);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchItem(); }, [id]);

  const callAction = async (action: string, body?: Record<string, any>) => {
    setActionLoading(action);
    try {
      const res = await fetch(`${API_URL}/api/admin/notice-inbox/${id}/${action}`, {
        method: action === "status" ? "GET" : "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `${action} failed`);
      showToast(`${action.charAt(0).toUpperCase() + action.slice(1)} successful!`, "success");
      await fetchItem();
    } catch (e: any) {
      showToast(e.message ?? `${action} failed`, "error");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
    </div>
  );

  if (error || !item) return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <AlertCircle className="h-10 w-10 text-red-400" />
      <p className="text-red-600">{error ?? "Notice not found"}</p>
      <button onClick={() => navigate("/admin/notice-inbox")} className="text-sm text-indigo-600 underline">
        Back to Inbox
      </button>
    </div>
  );

  const { source, import_record } = item;
  const status = import_record?.status ?? "new";
  const ai = import_record?.ai_extracted_json;

  return (
    <div className="flex-1 p-4 md:p-8 pt-6 max-w-5xl mx-auto space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
          toast.type === "success" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"
        }`}>
          {toast.msg}
        </div>
      )}

      {/* Back + header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/admin/notice-inbox")}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-600" />
        </button>
        <div className="flex-1">
          <h2 className="text-xl font-bold">Notice Import Detail</h2>
          <p className="text-xs text-gray-500">
            Source: {source.group_name} · {source.sender}
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Pipeline indicator */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm overflow-x-auto">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Import Pipeline</h3>
        <PipelineIndicator status={status} />
      </div>

      {/* Demo source banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center gap-2">
        <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0" />
        <p className="text-xs text-amber-700">
          <strong>Demo Source — Not connected to real WhatsApp.</strong> This message simulates how
          Nexora would receive notices from a college communication channel.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Original source message */}
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            {/* WhatsApp header */}
            <div className="bg-[#075E54] px-4 py-3 flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[#128C7E] flex items-center justify-center">
                <MessageSquare className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-white text-sm font-semibold">{source.group_name}</p>
                <p className="text-green-200 text-xs">{source.sender}</p>
              </div>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">
                  {new Date(source.timestamp).toLocaleString("en-IN")}
                </span>
                <span className="text-xs text-gray-400">ID: {source.source_message_id}</span>
              </div>
              <div className="bg-[#DCF8C6] rounded-lg rounded-tl-none p-3">
                <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {source.message_text}
                </p>
              </div>

              {source.attachment_name && (
                <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-4 w-4 text-red-500" />
                    <span className="text-xs font-medium text-gray-700">{source.attachment_name}</span>
                  </div>
                  {source.attachment_content && (
                    <div className="bg-white border border-gray-100 rounded p-2 max-h-40 overflow-y-auto">
                      <p className="text-xs text-gray-600 whitespace-pre-wrap">{source.attachment_content}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="text-xs text-gray-400 font-mono">
                Hash: {source.content_hash.slice(0, 20)}…
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">Actions</h3>

            {status === "new" && (
              <button
                onClick={() => callAction("import")}
                disabled={!!actionLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {actionLoading === "import" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Import into Nexora
              </button>
            )}

            {(status === "imported" || status === "draft") && (
              <button
                onClick={() => callAction("process")}
                disabled={!!actionLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {actionLoading === "process" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Process with Nexora AI
              </button>
            )}

            {["draft", "imported", "pending_approval"].includes(status) && (
              <div className="space-y-2">
                <button
                  onClick={() => callAction("approve", { title: draftTitle || undefined, content: draftContent || undefined })}
                  disabled={!!actionLoading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                >
                  {actionLoading === "approve" ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                  Approve Draft
                </button>
                <button
                  onClick={() => setShowRejectModal(true)}
                  disabled={!!actionLoading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-red-50 hover:bg-red-100 text-red-700 text-sm font-medium rounded-lg border border-red-200 transition-colors disabled:opacity-50"
                >
                  <XCircle className="h-4 w-4" />
                  Reject
                </button>
              </div>
            )}

            {status === "approved" && (
              <button
                onClick={() => callAction("publish")}
                disabled={!!actionLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {actionLoading === "publish" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Publish to College Portal
              </button>
            )}

            {status === "published" && (
              <div className="flex items-center gap-2 text-green-700 bg-green-50 rounded-lg p-3 text-sm">
                <CheckCircle className="h-4 w-4" />
                <span>Published to college portal. Indexed for RAG search.</span>
              </div>
            )}

            {import_record?.processing_error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700">
                <strong>Error:</strong> {import_record.processing_error}
              </div>
            )}
          </div>
        </div>

        {/* Right: Draft / AI data */}
        <div className="space-y-4">
          {/* Draft editor */}
          {import_record && (
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 space-y-4">
              <div className="flex items-center gap-2">
                <Edit3 className="h-4 w-4 text-purple-600" />
                <h3 className="text-sm font-semibold text-gray-700">Notice Draft</h3>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Title</label>
                  <input
                    type="text"
                    value={draftTitle}
                    onChange={e => setDraftTitle(e.target.value)}
                    disabled={["published", "rejected"].includes(status)}
                    placeholder="Notice title…"
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300 disabled:bg-gray-50 disabled:text-gray-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Content</label>
                  <textarea
                    value={draftContent}
                    onChange={e => setDraftContent(e.target.value)}
                    disabled={["published", "rejected"].includes(status)}
                    rows={8}
                    placeholder="Notice content…"
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none disabled:bg-gray-50 disabled:text-gray-500"
                  />
                </div>
                {!["published", "rejected"].includes(status) && (
                  <button
                    onClick={() => callAction("draft", { title: draftTitle, content: draftContent })}
                    disabled={!!actionLoading}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
                  >
                    {actionLoading === "draft" ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
                    Save Draft
                  </button>
                )}
              </div>
            </div>
          )}

          {/* AI extracted info */}
          {ai && (
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-4 w-4 text-indigo-500" />
                <h3 className="text-sm font-semibold text-gray-700">AI Extracted Information</h3>
                <span className="text-xs text-gray-400 ml-auto">(Do not rely on AI for official values)</span>
              </div>
              <div className="space-y-2 text-xs">
                {Object.entries(ai).map(([k, v]) => {
                  if (!v || (Array.isArray(v) && v.length === 0)) return null;
                  return (
                    <div key={k} className="flex gap-2">
                      <span className="text-gray-500 font-medium capitalize min-w-[100px] flex-shrink-0">
                        {k.replace(/_/g, " ")}:
                      </span>
                      <span className="text-gray-800">
                        {Array.isArray(v) ? v.join(", ") : String(v)}
                      </span>
                    </div>
                  );
                })}
              </div>
              <p className="text-xs text-amber-600 bg-amber-50 rounded p-2 mt-3">
                ⚠️ AI extraction is a guide only. Always verify official identifiers against the original source message.
              </p>
            </div>
          )}

          {/* Timeline */}
          {import_record && (
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Clock className="h-4 w-4 text-gray-500" />
                Timeline
              </h3>
              <div className="space-y-2 text-xs">
                {[
                  { label: "Imported", time: import_record.imported_at },
                  { label: "AI Processed", time: import_record.processed_at },
                  { label: "Approved", time: import_record.approved_at },
                  { label: "Rejected", time: import_record.rejected_at },
                  { label: "Published", time: import_record.published_at },
                ].filter(t => t.time).map(t => (
                  <div key={t.label} className="flex justify-between items-center">
                    <span className="text-gray-500">{t.label}</span>
                    <span className="text-gray-700">{new Date(t.time!).toLocaleString("en-IN")}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reject modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm space-y-4">
            <h3 className="font-semibold text-gray-900">Reject Notice</h3>
            <p className="text-sm text-gray-600">
              Rejected notices will not be published to students. Provide an optional reason.
            </p>
            <textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder="Reason for rejection (optional)"
              rows={3}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-300 resize-none"
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 py-2 text-sm border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  setShowRejectModal(false);
                  await callAction("reject", { reason: rejectReason || undefined });
                }}
                className="flex-1 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Confirm Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
