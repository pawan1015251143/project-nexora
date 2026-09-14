import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { API_URL } from "../config";
import AskNexoraContextual from "../components/AskNexoraContextual";
import { Sparkles, Award } from "lucide-react";
import { Button } from "../components/ui/button";

interface MarksRecord {
  id: number;
  subject_name: string;
  marks_obtained: number;
  total_marks: number;
  grade: string;
  semester: number;
}

export default function Marks() {
  const [records, setRecords] = useState<MarksRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAiOpen, setIsAiOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch(`${API_URL}/api/student/marks`, {
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
        <h2 className="text-3xl font-bold tracking-tight">Marks & Results</h2>
        <Button onClick={() => setIsAiOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700">
          <Sparkles className="h-4 w-4" />
          Ask AI about Marks
        </Button>
      </div>

      <AskNexoraContextual
        isOpen={isAiOpen}
        onClose={() => setIsAiOpen(false)}
        contextType="marks"
        contextTitle="your Marks & Results"
        suggestions={["What is my highest scoring subject?", "Am I failing any subject?", "What is the passing criteria?"]}
      />

      {loading ? (
        <div>Loading marks data...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {records.map(record => (
            <Card key={record.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{record.subject_name}</CardTitle>
                <Award className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {record.marks_obtained} / {record.total_marks}
                </div>
                <div className="flex justify-between items-center mt-2">
                  <p className="text-sm text-gray-500">Grade: <span className="font-semibold text-gray-900 dark:text-gray-100">{record.grade}</span></p>
                  <p className="text-xs text-gray-400">Semester {record.semester}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
