import React from "react";
import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, MessageSquare, Search, Bell, BookOpen, FileText, Settings, Users, FolderOpen, Activity, X, CalendarCheck, Award, CreditCard, Inbox } from "lucide-react";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";


interface SidebarProps {
  role?: "student" | "faculty" | "admin";
  onClose?: () => void;
}

export function Sidebar({ role = "student", onClose }: SidebarProps) {
  const location = useLocation();

  const routes = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard, roles: ["student", "faculty", "admin"] },
    { name: "AI Assistant", path: "/chat", icon: MessageSquare, roles: ["student", "faculty", "admin"] },
    { name: "Global Search", path: "/search", icon: Search, roles: ["student", "faculty", "admin"] },
    { name: "PDF Q&A", path: "/pdf-qa", icon: FileText, roles: ["student", "faculty", "admin"] },
    { name: "Attendance", path: "/attendance", icon: CalendarCheck, roles: ["student"] },
    { name: "Marks/Results", path: "/marks", icon: Award, roles: ["student"] },
    { name: "Fees", path: "/fees", icon: CreditCard, roles: ["student"] },
    { name: "Notices", path: "/notices", icon: Bell, roles: ["student", "faculty", "admin"] },
    { name: "Resources", path: "/resources", icon: BookOpen, roles: ["student", "faculty"] },
    { name: "Document Manager", path: "/admin/docs", icon: FolderOpen, roles: ["admin", "faculty"] },
    { name: "User Manager", path: "/admin/users", icon: Users, roles: ["admin"] },
    { name: "Notice Inbox", path: "/admin/notice-inbox", icon: Inbox, roles: ["admin"] },
    { name: "Analytics", path: "/admin/analytics", icon: Activity, roles: ["admin"] },
  ];

  const filteredRoutes = routes.filter(r => r.roles.includes(role));

  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 shadow-lg lg:shadow-none transition-colors duration-200">
      <div className="flex h-14 items-center justify-between border-b border-gray-200 px-4 lg:h-[60px] dark:border-gray-800">
        <Link to="/" className="flex items-center gap-2 font-semibold" onClick={onClose}>
          <div className="h-6 w-6 rounded-full bg-indigo-600 flex items-center justify-center">
            <span className="text-white text-xs font-bold">N</span>
          </div>
          <span className="text-lg">Nexora</span>
        </Link>
        {onClose && (
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClose}>
            <X className="h-5 w-5" />
            <span className="sr-only">Close sidebar</span>
          </Button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="grid items-start px-2 text-sm font-medium gap-1">
          {filteredRoutes.map((route) => {
            const Icon = route.icon;
            const isActive = location.pathname.startsWith(route.path);
            return (
              <Link
                key={route.path}
                to={route.path}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 transition-all",
                  isActive 
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 font-semibold" 
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-indigo-700 dark:text-indigo-400" : "text-gray-500 dark:text-gray-400")} />
                {route.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
