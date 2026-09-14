import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { API_URL } from "../config";
import AskNexoraContextual from "../components/AskNexoraContextual";
import { Sparkles, CalendarCheck } from "lucide-react";
import { Button } from "../components/ui/button";

interface AttendanceRecord {
  id: number;
  subject_name: string;
  total_classes: number;
  attended_classes: number;
  percentage: number;
  semester: number;
}

export default function Attendance() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAiOpen, setIsAiOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch(`${API_URL}/api/student/attendance`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
      setRecords(data);
      setLoading(false);
    })
    .catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6 relative">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Attendance</h2>
        <Button onClick={() => setIsAiOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700">
          <Sparkles className="h-4 w-4" />
          Ask AI about Attendance
        </Button>
      </div>

      <AskNexoraContextual
        isOpen={isAiOpen}
        onClose={() => setIsAiOpen(false)}
        contextType="attendance"
        contextTitle="your Attendance"
        suggestions={["Am I eligible for exams?", "Which subject has the lowest attendance?", "What is the minimum attendance requirement?"]}
      />

      {loading ? (
        <div>Loading attendance data...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {records.map(record => (
            <Card key={record.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{record.subject_name}</CardTitle>
                <CalendarCheck className="h-4 w-4 text-indigo-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold" style={{ color: record.percentage >= 75 ? 'green' : 'red' }}>
                  {record.percentage.toFixed(1)}%
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Attended: {record.attended_classes} / {record.total_classes}
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2.5 mt-3 dark:bg-gray-700">
                  <div className="bg-indigo-600 h-2.5 rounded-full" style={{ width: `${record.percentage}%` }}></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
