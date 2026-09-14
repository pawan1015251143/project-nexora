import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "../components/ui/card";
import { API_URL } from "../config";
import AskNexoraContextual from "../components/AskNexoraContextual";
import { Sparkles, CreditCard, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "../components/ui/button";

interface FeeRecord {
  id: number;
  total_fee: number;
  paid_fee: number;
  pending_fee: number;
  due_date: string;
  semester: number;
}

export default function Fees() {
  const [records, setRecords] = useState<FeeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAiOpen, setIsAiOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch(`${API_URL}/api/student/fees`, {
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
        <h2 className="text-3xl font-bold tracking-tight">Fee Status</h2>
        <Button onClick={() => setIsAiOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700">
          <Sparkles className="h-4 w-4" />
          Ask AI about Fees
        </Button>
      </div>

      <AskNexoraContextual
        isOpen={isAiOpen}
        onClose={() => setIsAiOpen(false)}
        contextType="fees"
        contextTitle="your Fees & Dues"
        suggestions={["When is my next fee due?", "What is the penalty for late fee submission?", "How can I pay my fees online?"]}
      />

      {loading ? (
        <div>Loading fees data...</div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {records.map(record => {
            const isFullyPaid = record.pending_fee <= 0;
            return (
              <Card key={record.id} className={isFullyPaid ? "border-green-200 bg-green-50/10 dark:border-green-900/30 dark:bg-green-900/5" : "border-red-200 bg-red-50/10 dark:border-red-900/30 dark:bg-red-900/5"}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 border-b border-gray-100 dark:border-gray-800">
                  <CardTitle className="text-lg font-semibold flex items-center gap-2">
                    <CreditCard className="h-5 w-5 text-gray-500" />
                    Semester {record.semester} Fees
                  </CardTitle>
                  {isFullyPaid ? (
                    <span className="flex items-center text-sm font-medium text-green-600 dark:text-green-500 bg-green-100 dark:bg-green-900/30 px-2 py-1 rounded-md">
                      <CheckCircle className="w-4 h-4 mr-1" /> Paid
                    </span>
                  ) : (
                    <span className="flex items-center text-sm font-medium text-red-600 dark:text-red-500 bg-red-100 dark:bg-red-900/30 px-2 py-1 rounded-md">
                      <AlertCircle className="w-4 h-4 mr-1" /> Due
                    </span>
                  )}
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Total Amount:</span>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">₹{record.total_fee.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Paid Amount:</span>
                      <span className="font-semibold text-green-600 dark:text-green-500">₹{record.paid_fee.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t border-gray-100 dark:border-gray-800">
                      <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Pending Amount:</span>
                      <span className={`text-lg font-bold ${isFullyPaid ? 'text-gray-500' : 'text-red-600 dark:text-red-500'}`}>
                        ₹{record.pending_fee.toLocaleString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
                {!isFullyPaid && (
                  <CardFooter className="bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center py-3 border-t border-gray-100 dark:border-gray-800">
                    <span className="text-xs text-red-500 font-medium flex items-center">
                      <AlertCircle className="w-3 h-3 mr-1" /> Due Date: {new Date(record.due_date).toLocaleDateString()}
                    </span>
                    <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700">Pay Now</Button>
                  </CardFooter>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
