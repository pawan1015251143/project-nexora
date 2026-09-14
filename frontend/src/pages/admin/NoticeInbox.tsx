import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  MessageSquare, Inbox, Clock, CheckCircle, XCircle,
  Upload, Loader2, AlertCircle, RefreshCw, Eye
} from "lucide-react";
import { API_URL } from "../../config";

// ── Types ────────────────────────────────────────────────────────────────────

interface DemoSourceMessage {
  id: number;
  source_message_id: string;
  group_name: string;
  sender: string;
  message_text: string;
  attachment_name?: string;
  attachment_type?: string;
  timestamp: string;
  imported: boolean;
  content_hash: string;
}

interface NoticeImportRecord {
  id: number;
  status: string;
  draft_title?: string;
  processing_error?: string;
  imported_at?: string;
  processed_at?: string;
  approved_at?: string;
  published_at?: string;
  notice_id?: number;
}

interface InboxItem {
  source: DemoSourceMessage;
  import_record?: NoticeImportRecord;
}

// ── Status badge ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  new: { label: "New", color: "bg-sky-100 text-sky-800 border-sky-200" },
  imported: { label: "Imported", color: "bg-blue-100 text-blue-800 border-blue-200" },
  processing: { label: "Processing", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  draft: { label: "Draft", color: "bg-purple-100 text-purple-800 border-purple-200" },
  pending_approval: { label: "Pending Approval", color: "bg-orange-100 text-orange-800 border-orange-200" },
  approved: { label: "Approved", color: "bg-emerald-100 text-emerald-800 border-emerald-200" },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800 border-red-200" },
  published: { label: "Published ✓", color: "bg-green-100 text-green-800 border-green-200" },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: "bg-gray-100 text-gray-700 border-gray-200" };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

// ── WhatsApp-style message card ───────────────────────────────────────────────

function WhatsAppCard({ item, onImport, importing }: {
  item: InboxItem;
  onImport: (id: number) => void;
  importing: boolean;
}) {
  const { source, import_record } = item;
  const status = import_record?.status ?? "new";
  const canImport = !import_record;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      {/* WhatsApp-style header */}
      <div className="bg-[#075E54] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#128C7E] flex items-center justify-center">
            <MessageSquare className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="text-white text-sm font-semibold">{source.group_name}</p>
            <p className="text-green-200 text-xs">Demo Source — Not connected to real WhatsApp</p>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Message body */}
      <div className="p-4">
        {/* Sender + time */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-[#128C7E]">{source.sender}</span>
          <span className="text-xs text-gray-400">
            {new Date(source.timestamp).toLocaleDateString("en-IN", {
              day: "2-digit", month: "short", year: "numeric",
              hour: "2-digit", minute: "2-digit"
            })}
          </span>
        </div>

        {/* Message preview */}
        <div className="bg-[#DCF8C6] rounded-lg rounded-tl-none p-3 mb-3 max-h-28 overflow-hidden relative">
          <p className="text-sm text-gray-800 whitespace-pre-line leading-relaxed">
            {source.message_text.length > 240
              ? source.message_text.slice(0, 240) + "…"
              : source.message_text}
          </p>
          {source.message_text.length > 240 && (
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-[#DCF8C6] to-transparent" />
          )}
        </div>

        {/* Attachment */}
        {source.attachment_name && (
          <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 mb-3">
            <div className="w-8 h-8 rounded bg-red-100 flex items-center justify-center flex-shrink-0">
              <span className="text-red-600 text-xs font-bold uppercase">
                {source.attachment_type?.toUpperCase() ?? "FILE"}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-700 truncate">{source.attachment_name}</p>
              <p className="text-xs text-gray-400">Simulated attachment</p>
            </div>
          </div>
        )}

        {/* Draft title (if processed) */}
        {import_record?.draft_title && (
          <div className="text-xs text-purple-700 bg-purple-50 rounded px-2 py-1 mb-3">
            📝 Draft: {import_record.draft_title}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
          {canImport ? (
            <button
              onClick={() => onImport(source.id)}
              disabled={importing}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {importing ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Upload className="h-3 w-3" />
              )}
              Import into Nexora
            </button>
          ) : (
            <Link
              to={`/admin/notice-inbox/${source.id}`}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-medium rounded-lg transition-colors"
            >
              <Eye className="h-3 w-3" />
              View & Review
            </Link>
          )}

          {import_record?.processing_error && (
            <span className="flex items-center gap-1 text-xs text-red-600">
              <AlertCircle className="h-3 w-3" />
              Error
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function NoticeInbox() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importingId, setImportingId] = useState<number | null>(null);
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  const token = localStorage.getItem("access_token");

  const fetchInbox = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/admin/notice-inbox`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Failed to load inbox (${res.status})`);
      const data = await res.json();
      setItems(data);
    } catch (e: any) {
      setError(e.message ?? "Failed to load the notice inbox.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchInbox(); }, []);

  const showToast = (msg: string, type: "success" | "error") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleImport = async (msgId: number) => {
    setImportingId(msgId);
    try {
      const res = await fetch(`${API_URL}/api/admin/notice-inbox/${msgId}/import`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.status === 409) {
        showToast(data.detail, "error");
        return;
      }
      if (!res.ok) throw new Error(data.detail ?? "Import failed");
      showToast("Notice imported successfully!", "success");
      await fetchInbox();
    } catch (e: any) {
      showToast(e.message ?? "Import failed", "error");
    } finally {
      setImportingId(null);
    }
  };

  // Stats
  const total = items.length;
  const newCount = items.filter(i => !i.import_record).length;
  const publishedCount = items.filter(i => i.import_record?.status === "published").length;
  const pendingCount = items.filter(i =>
    i.import_record && !["published", "rejected"].includes(i.import_record.status)
  ).length;

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
          toast.type === "success" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"
        }`}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Inbox className="h-6 w-6 text-indigo-600" />
            Notice Inbox
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Simulated notices from the ABC College WhatsApp group demo source.
            Review, process, and publish to the college portal.
          </p>
        </div>
        <button
          onClick={fetchInbox}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Demo warning banner */}
      <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
        <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-amber-800">Demo Source — Not connected to real WhatsApp</p>
          <p className="text-xs text-amber-700 mt-0.5">
            These messages are simulated for demonstration purposes. In a real deployment, notices would be
            received from the college's official communication channels.
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Messages", value: total, color: "text-gray-800" },
          { label: "New / Unimported", value: newCount, color: "text-sky-600" },
          { label: "Pending Review", value: pendingCount, color: "text-orange-600" },
          { label: "Published", value: publishedCount, color: "text-emerald-600" },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <AlertCircle className="h-10 w-10 text-red-400" />
          <p className="text-red-600 font-medium">{error}</p>
          <button onClick={fetchInbox} className="text-sm text-indigo-600 underline">Try again</button>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <Inbox className="h-12 w-12 text-gray-300" />
          <p className="text-gray-500 font-medium">No messages in the inbox</p>
          <p className="text-xs text-gray-400">Run the seed script to populate demo messages.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map(item => (
            <WhatsAppCard
              key={item.source.id}
              item={item}
              onImport={handleImport}
              importing={importingId === item.source.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
