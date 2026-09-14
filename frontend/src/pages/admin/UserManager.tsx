import React from "react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { UserPlus, UserCog, Trash2 } from "lucide-react";

export default function UserManager() {
  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">User Manager</h2>
          <p className="text-gray-500">Manage student and faculty accounts.</p>
        </div>
        <Button><UserPlus className="mr-2 h-4 w-4" /> Add User</Button>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Registered Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border dark:border-gray-800 overflow-x-auto">
            <table className="w-full text-sm text-left whitespace-nowrap min-w-[600px]">
              <thead className="bg-gray-50 dark:bg-gray-900 text-gray-500 uppercase">
                <tr>
                  <th className="px-6 py-3 font-medium">Name</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Role</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y dark:divide-gray-800">
                <tr className="bg-white dark:bg-gray-950">
                  <td className="px-6 py-4 font-medium">Pawan Kumar</td>
                  <td className="px-6 py-4">pawan@college.edu</td>
                  <td className="px-6 py-4"><span className="text-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 px-2 py-1 rounded-full text-xs font-semibold capitalize">Student</span></td>
                  <td className="px-6 py-4 text-right">
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"><UserCog className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"><Trash2 className="h-4 w-4" /></Button>
                  </td>
                </tr>
                <tr className="bg-white dark:bg-gray-950">
                  <td className="px-6 py-4 font-medium">Dr. Jane Smith</td>
                  <td className="px-6 py-4">jane.smith@college.edu</td>
                  <td className="px-6 py-4"><span className="text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded-full text-xs font-semibold capitalize">Faculty</span></td>
                  <td className="px-6 py-4 text-right">
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"><UserCog className="h-4 w-4" /></Button>
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
