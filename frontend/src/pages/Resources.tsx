import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { FileText, Download, ExternalLink } from "lucide-react";

export default function Resources() {
  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Academic Resources</h2>
      </div>
      
      <div className="grid gap-4 mt-4 md:grid-cols-2 lg:grid-cols-3">
        {[1,2,3,4,5,6].map(i => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CS301 - Database Systems</CardTitle>
              <FileText className="h-4 w-4 text-indigo-500" />
            </CardHeader>
            <CardContent>
              <h3 className="font-bold text-lg mt-2">Fall 2026 Syllabus</h3>
              <p className="text-xs text-gray-500 mb-4">Uploaded 2 weeks ago</p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="w-full text-xs h-8"><Download className="mr-2 h-3 w-3"/> Download</Button>
                <Button variant="default" size="sm" className="w-full text-xs h-8"><ExternalLink className="mr-2 h-3 w-3"/> Chat with PDF</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
