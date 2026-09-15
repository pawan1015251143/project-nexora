import React, { useState, useEffect } from "react";
import { Search, Megaphone, Calendar, Clock, Plus, Edit, Trash2, Languages, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { cn } from "../lib/utils";
import { API_URL } from "../config";
import { getAuthToken } from "../lib/auth";

type Notice = {
  id: number;
  title: string;
  content: string;
  priority: number;
  published_at: string;
  expires_at?: string;
  department_id?: number;
};

export default function Notices() {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [activeModes, setActiveModes] = useState<Record<number, string>>({});
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [translating, setTranslating] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const fetchProfile = async () => {
      const token = getAuthToken();
      if (!token) return;
      try {
        const res = await fetch(`${API_URL}/api/auth/me`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const user = await res.json();
          setIsAdmin(user.role === "admin");
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchProfile();
    fetchNotices();
  }, []);

  const fetchNotices = async (query = "") => {
    const token = getAuthToken();
    let url = `${API_URL}/api/notices`;
    if (query) {
      url += `?search_query=${encodeURIComponent(query)}`;
    }
    
    try {
      const res = await fetch(url, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setNotices(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchNotices(searchQuery);
  };

  const getPriorityColor = (priority: number) => {
    switch(priority) {
      case 2: return "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-300";
      case 1: return "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300";
      default: return "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300";
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch(priority) {
      case 2: return "Urgent";
      case 1: return "High";
      default: return "Normal";
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this notice?")) return;
    const token = getAuthToken();
    try {
      const res = await fetch(`${API_URL}/api/notices/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        fetchNotices(searchQuery);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleModeChange = async (noticeId: number, mode: string) => {
    if (mode === "en_original") {
      setActiveModes(prev => ({ ...prev, [noticeId]: mode }));
      return;
    }

    const cacheKey = `${noticeId}_${mode}`;
    if (translations[cacheKey]) {
      setActiveModes(prev => ({ ...prev, [noticeId]: mode }));
      return;
    }

    setTranslating(prev => ({ ...prev, [noticeId]: true }));
    const token = getAuthToken();
    
    try {
      const res = await fetch(`${API_URL}/api/notices/${noticeId}/translation?mode=${mode}`, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setTranslations(prev => ({ ...prev, [cacheKey]: data.content }));
        setActiveModes(prev => ({ ...prev, [noticeId]: mode }));
      } else {
        alert("Translation service is currently unavailable. Showing original text.");
        setActiveModes(prev => ({ ...prev, [noticeId]: "en_original" }));
      }
    } catch (err) {
      console.error(err);
      alert("An error occurred while fetching translation.");
      setActiveModes(prev => ({ ...prev, [noticeId]: "en_original" }));
    } finally {
      setTranslating(prev => ({ ...prev, [noticeId]: false }));
    }
  };

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Campus Notices</h2>
          <p className="text-gray-500 dark:text-gray-400">Important announcements and updates.</p>
        </div>
        
        {isAdmin && (
          <Button>
            <Plus className="mr-2 h-4 w-4" /> New Notice
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1 flex gap-2 w-full">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Search notices..."
                className="pl-9"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button type="submit">Search</Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {notices.map((notice) => (
          <Card key={notice.id} className="overflow-hidden">
            <div className={cn("h-1 w-full", notice.priority === 2 ? "bg-red-500" : notice.priority === 1 ? "bg-amber-500" : "bg-blue-500")} />
            <CardContent className="p-6">
              <div className="flex justify-between items-start gap-4">
                <div className="space-y-1 w-full">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className={cn("text-xs font-medium px-2.5 py-0.5 rounded-full border", getPriorityColor(notice.priority))}>
                      {getPriorityLabel(notice.priority)}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center">
                      <Calendar className="mr-1 h-3 w-3" />
                      {new Date(notice.published_at).toLocaleDateString()}
                    </span>
                    {notice.expires_at && (
                      <span className="text-xs text-gray-500 flex items-center ml-2">
                        <Clock className="mr-1 h-3 w-3" />
                        Valid until: {new Date(notice.expires_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <h3 className="text-xl font-semibold tracking-tight">{notice.title}</h3>
                  <div className="flex items-center gap-2 mt-3 mb-1">
                    <Languages className="h-4 w-4 text-gray-400" />
                    <select 
                      className="text-sm bg-gray-50 border border-gray-200 text-gray-700 rounded-md px-2 py-1 dark:bg-gray-800/50 dark:border-gray-700 dark:text-gray-300 outline-none focus:ring-1 focus:ring-blue-500 transition-all cursor-pointer"
                      value={activeModes[notice.id] || "en_original"}
                      onChange={(e) => handleModeChange(notice.id, e.target.value)}
                      disabled={translating[notice.id]}
                    >
                      <option value="en_original">🇬🇧 Original English</option>
                      <option value="hi_annotated">🇬🇧 + 🇮🇳 English + Hindi Meaning</option>
                      <option value="hi_full">🇮🇳 हिंदी में पढ़ें (Translation)</option>
                    </select>
                    {translating[notice.id] && <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />}
                  </div>
                  <div className="mt-2 text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                    {translating[notice.id] ? (
                      <div className="animate-pulse flex space-x-4 py-2">
                        <div className="flex-1 space-y-3">
                          <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded"></div>
                          <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
                          <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded w-4/6"></div>
                        </div>
                      </div>
                    ) : (
                      (activeModes[notice.id] || "en_original") === "en_original" 
                        ? notice.content 
                        : translations[`${notice.id}_${activeModes[notice.id]}`] || notice.content
                    )}
                  </div>
                </div>
                
                {isAdmin && (
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(notice.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
        {notices.length === 0 && (
          <div className="text-center p-12 text-gray-500 border border-dashed rounded-xl bg-gray-50/50 dark:bg-gray-900/50 dark:border-gray-800">
            <Megaphone className="h-12 w-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">No notices found</h3>
            <p className="mt-1 text-sm text-gray-500">There are no announcements matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}
