import React, { useState, useEffect } from "react";
import { 
  Users, UserCheck, FileText, CheckCircle, 
  MessageSquare, MessageCircle, AlertCircle, ThumbsUp, ThumbsDown
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell
} from "recharts";
import { API_URL } from "../../config";
import { getAuthToken } from "../../lib/auth";

type Metrics = {
  total_students: number;
  total_faculty: number;
  total_documents: number;
  approved_documents: number;
  questions_today: number;
  total_questions: number;
  unanswered_questions: number;
  positive_feedback: number;
  negative_feedback: number;
};

type ChartData = {
  questions_over_time: any[];
  popular_categories: any[];
  popular_documents: any[];
  department_usage: any[];
  feedback_trends: any[];
};

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Analytics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [charts, setCharts] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const token = getAuthToken();
    if (!token) {
      setError("Not authorized");
      setLoading(false);
      return;
    }
    try {
      const [metricsRes, chartsRes] = await Promise.all([
        fetch(`${API_URL}/api/analytics/metrics`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${API_URL}/api/analytics/charts`, { headers: { "Authorization": `Bearer ${token}` } })
      ]);

      if (!metricsRes.ok || !chartsRes.ok) {
        setError("Failed to fetch analytics data. You might not have admin privileges.");
      } else {
        setMetrics(await metricsRes.json());
        setCharts(await chartsRes.json());
      }
    } catch (err) {
      setError("Network error fetching analytics.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight mb-4">Analytics Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
            <Card key={i}><CardContent className="h-24 bg-gray-200 dark:bg-gray-800" /></Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 animate-pulse mt-8">
          <Card><CardContent className="h-80 bg-gray-200 dark:bg-gray-800" /></Card>
          <Card><CardContent className="h-80 bg-gray-200 dark:bg-gray-800" /></Card>
        </div>
      </div>
    );
  }

  if (error || !metrics || !charts) {
    return (
      <div className="flex-1 p-8 flex flex-col items-center justify-center text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">Access Denied</h2>
        <p className="text-gray-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6 max-w-7xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h2>
          <p className="text-gray-500">Monitor system usage, knowledge base health, and user feedback.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">Total Students</p>
                <p className="text-3xl font-bold">{metrics.total_students}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">Total Faculty</p>
                <p className="text-3xl font-bold">{metrics.total_faculty}</p>
              </div>
              <UserCheck className="h-8 w-8 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">Approved Docs</p>
                <p className="text-3xl font-bold">{metrics.approved_documents} <span className="text-sm font-normal text-gray-400">/ {metrics.total_documents}</span></p>
              </div>
              <CheckCircle className="h-8 w-8 text-indigo-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">Questions Today</p>
                <p className="text-3xl font-bold">{metrics.questions_today}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-amber-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-indigo-100 dark:bg-indigo-900/30 rounded-full text-indigo-600">
              <MessageCircle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Total Questions</p>
              <p className="text-xl font-bold">{metrics.total_questions}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full text-red-600">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Needs Review</p>
              <p className="text-xl font-bold">{metrics.unanswered_questions}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full text-green-600">
              <ThumbsUp className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Positive Feedback</p>
              <p className="text-xl font-bold">{metrics.positive_feedback}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-full text-orange-600">
              <ThumbsDown className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Negative Feedback</p>
              <p className="text-xl font-bold">{metrics.negative_feedback}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Questions Over Time (Last 30 Days)</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {charts.questions_over_time.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={charts.questions_over_time}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="count" stroke="#4f46e5" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">No data available</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Department Usage</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {charts.department_usage.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.department_usage}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">No data available</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Popular Document Categories</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {charts.popular_categories.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.popular_categories}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={120}
                    fill="#8884d8"
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent = 0 }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {charts.popular_categories.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">No data available</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Feedback Trends</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {charts.feedback_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={charts.feedback_trends}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Line type="monotone" dataKey="positive" stroke="#10b981" strokeWidth={2} />
                  <Line type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">No data available</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Top Retrieved Documents</CardTitle>
        </CardHeader>
        <CardContent>
          {charts.popular_documents.length > 0 ? (
            <div className="space-y-4">
              {charts.popular_documents.map((doc, idx) => (
                <div key={idx} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 font-bold">
                      {idx + 1}
                    </div>
                    <div>
                      <p className="font-medium">{doc.name}</p>
                    </div>
                  </div>
                  <div className="text-sm font-bold text-gray-500">
                    {doc.value} retrievals
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">No data available</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
