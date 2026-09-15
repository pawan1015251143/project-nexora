import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../components/ui/card";
import { API_URL } from "../config";
import { setAuthToken } from "../lib/auth";

export default function Register() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      // 1. Register user
      const regRes = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role })
      });

      if (!regRes.ok) {
        const errData = await regRes.json().catch(() => ({}));
        throw new Error(errData.detail || "Registration failed");
      }

      // 2. Automatically log in after registration
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const loginRes = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString()
      });

      if (!loginRes.ok) {
        // If auto-login fails, redirect to /login page
        navigate("/login");
        return;
      }

      const loginData = await loginRes.json();
      if (loginData.access_token) {
        setAuthToken(loginData.access_token);
        navigate("/dashboard");
      } else {
        navigate("/login");
      }
    } catch (err: any) {
      setError(err.message || "An error occurred during registration");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-950 py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center">
              <span className="text-white font-bold">N</span>
            </div>
          </div>
          <CardTitle className="text-2xl">Create an account</CardTitle>
          <CardDescription>Join Nexora as a student or faculty</CardDescription>
        </CardHeader>
        <form onSubmit={handleRegister}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none" htmlFor="name">Full Name</label>
              <Input id="name" placeholder="John Doe" required value={name} onChange={(e) => setName(e.target.value)} disabled={isLoading} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none" htmlFor="email">College Email</label>
              <Input id="email" type="email" placeholder="john@college.edu" required value={email} onChange={(e) => setEmail(e.target.value)} disabled={isLoading} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none" htmlFor="password">Password</label>
              <Input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} disabled={isLoading} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none" htmlFor="role">Role</label>
              <select id="role" value={role} onChange={(e) => setRole(e.target.value)} disabled={isLoading} className="flex h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-900">
                <option value="student">Student</option>
                <option value="faculty">Faculty</option>
              </select>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            {error && <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 w-full p-3 rounded-md border border-red-200 dark:border-red-800/50">{error}</div>}
            <Button className="w-full" type="submit" disabled={isLoading}>{isLoading ? "Creating account..." : "Register"}</Button>
            <div className="text-center text-sm text-gray-500 dark:text-gray-400">
              Already have an account?{" "}
              <Link to="/login" className="text-indigo-600 hover:underline dark:text-indigo-400">
                Sign in
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
