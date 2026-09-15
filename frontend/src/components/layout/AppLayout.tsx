import React, { useState, useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";
import { getAuthToken, parseJwtPayload } from "../../lib/auth";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<"student" | "faculty" | "admin">("student");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      const payload = parseJwtPayload(token);
      if (payload && payload.role) {
        setRole(payload.role);
      }
    }
  }, []);

  return (
    <div className="flex min-h-screen w-full flex-col bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-50 transition-colors duration-200">
      <div className="flex flex-1 h-screen overflow-hidden">
        {/* Mobile sidebar overlay */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setIsSidebarOpen(false)}
            aria-hidden="true"
          />
        )}
        
        {/* Sidebar container */}
        <div className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
          <Sidebar role={role} onClose={() => setIsSidebarOpen(false)} />
        </div>

        <div className="flex flex-col flex-1 overflow-hidden w-full lg:w-[calc(100%-16rem)] relative">
          <TopNav onMenuClick={() => setIsSidebarOpen(true)} />
          <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-slate-50 dark:bg-gray-900 transition-colors duration-200">
            <div className="mx-auto max-w-7xl">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
