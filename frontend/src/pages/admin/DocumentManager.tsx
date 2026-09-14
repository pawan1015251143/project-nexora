import React from "react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Upload, FileText, Trash2, Edit } from "lucide-react";

export default function DocumentManager() {
  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Document Manager</h2>
          <p className="text-gray-500">Upload and manage RAG context documents.</p>
        </div>
        <Button><Upload className="mr-2 h-4 w-4" /> Upload Document</Button>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Indexed Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border dark:border-gray-800 overflow-x-auto">
            <table className="w-full text-sm text-left whitespace-nowrap min-w-[600px]">
              <thead className="bg-gray-50 dark:bg-gray-900 text-gray-500 uppercase">
                <tr>
                  <th className="px-6 py-3 font-medium">Document Title</th>
                  <th className="px-6 py-3 font-medium">Department</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y dark:divide-gray-800">
                <tr className="bg-white dark:bg-gray-950">
                  <td className="px-6 py-4 flex items-center gap-2 font-medium">
                    <FileText className="h-4 w-4 text-indigo-500" /> CS301_Syllabus.pdf
                  </td>
                  <td className="px-6 py-4">Computer Science</td>
                  <td className="px-6 py-4"><span className="text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded-full text-xs font-semibold">Indexed</span></td>
                  <td className="px-6 py-4 text-right">
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"><Edit className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"><Trash2 className="h-4 w-4" /></Button>
                  </td>
                </tr>
                <tr className="bg-white dark:bg-gray-950">
                  <td className="px-6 py-4 flex items-center gap-2 font-medium">
                    <FileText className="h-4 w-4 text-indigo-500" /> Student_Handbook_2026.pdf
                  </td>
                  <td className="px-6 py-4">Global</td>
                  <td className="px-6 py-4"><span className="text-amber-600 bg-amber-50 dark:bg-amber-900/20 px-2 py-1 rounded-full text-xs font-semibold">Processing</span></td>
                  <td className="px-6 py-4 text-right">
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"><Edit className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"><Trash2 className="h-4 w-4" /></Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
