import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Bell, BookOpen, Clock, CalendarCheck, Award, CreditCard } from "lucide-react";
import { API_URL } from "../config";
import { getAuthToken, parseJwtPayload } from "../lib/auth";
import { useNavigate, Link } from "react-router-dom";

interface DashboardData {
  current_semester: number;
  overall_attendance: number;
  pending_fees: number;
  latest_percentage: number;
  recent_notices_count: number;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [role, setRole] = useState<string>("student");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = getAuthToken();
    let currentRole = "student";
    if (token) {
      const payload = parseJwtPayload(token);
      if (payload && payload.role) {
        currentRole = payload.role;
        setRole(currentRole);
      }
    }

    if (currentRole === "student" && token) {
      fetch(`${API_URL}/api/student/dashboard`, {
        headers: { "Authorization": `Bearer ${token}` }
      })
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch dashboard data");
        return res.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) {
    return <div className="p-8">Loading dashboard...</div>;
  }

  if (role !== "student") {
    return (
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Notices</CardTitle>
              <Bell className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">Manage Notices</div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Student Dashboard</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate("/attendance")}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-indigo-700">Overall Attendance</CardTitle>
            <CalendarCheck className="h-4 w-4 text-indigo-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.overall_attendance.toFixed(1)}%</div>
            <p className="text-xs text-gray-500">Semester {data?.current_semester}</p>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate("/marks")}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">Latest Result</CardTitle>
            <Award className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.latest_percentage.toFixed(1)}%</div>
            <p className="text-xs text-gray-500">From last exams</p>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate("/fees")}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-700">Pending Fees</CardTitle>
            <CreditCard className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{data?.pending_fees.toLocaleString()}</div>
            <p className="text-xs text-gray-500">Semester {data?.current_semester}</p>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate("/notices")}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Notices</CardTitle>
            <Bell className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.recent_notices_count}</div>
            <p className="text-xs text-gray-500">Campus announcements</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7 mt-4">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Link to="/chat" className="flex items-center p-3 rounded-lg border hover:bg-indigo-50 transition-colors">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none text-indigo-700">Ask Nexora AI</p>
                  <p className="text-sm text-gray-500">Get quick answers about your courses or policies</p>
                </div>
              </Link>
              <Link to="/attendance" className="flex items-center p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none">View Attendance Details</p>
                  <p className="text-sm text-gray-500">Check subject-wise attendance</p>
                </div>
              </Link>
              <Link to="/fees" className="flex items-center p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none">Pay Pending Fees</p>
                  <p className="text-sm text-gray-500">Clear your dues for Semester {data?.current_semester}</p>
                </div>
              </Link>
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Academic Calendar</CardTitle>
            <CardDescription>Upcoming events</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex flex-col gap-1 border-b pb-2">
                <span className="font-medium text-sm">Mid-Term Examinations</span>
                <span className="text-xs text-red-500 font-semibold">Starts in 2 weeks</span>
              </div>
              <div className="flex flex-col gap-1 border-b pb-2">
                <span className="font-medium text-sm">Fee Submission Deadline</span>
                <span className="text-xs text-red-500 font-semibold">Next Friday</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
