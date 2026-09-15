import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { clearAuthToken } from "../lib/auth";
import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";

export default function Profile() {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuthToken();
    navigate("/login");
  };

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6 max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold tracking-tight">Profile Settings</h2>
      
      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-500">Full Name</label>
              <p className="font-medium">Student User</p>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-500">Email</label>
              <p className="font-medium">student@college.edu</p>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-500">Department</label>
              <p className="font-medium">Computer Science</p>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-500">Role</label>
              <p className="font-medium capitalize">student</p>
            </div>
          </div>
          <div className="pt-4 flex gap-3">
            <Button variant="outline">Edit Profile</Button>
            <Button variant="danger" onClick={handleLogout} className="flex items-center gap-2">
              <LogOut className="h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
