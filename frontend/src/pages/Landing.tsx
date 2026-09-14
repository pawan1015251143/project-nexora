import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { ArrowRight, Sparkles, BookOpen, Shield } from "lucide-react";

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-50">
      <header className="flex h-16 items-center px-4 lg:px-8 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-2 font-bold text-xl">
          <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">N</span>
          </div>
          Nexora
        </div>
        <nav className="ml-auto flex items-center gap-4">
          <Link to="/login">
            <Button variant="ghost">Sign In</Button>
          </Link>
          <Link to="/register">
            <Button>Get Started</Button>
          </Link>
        </nav>
      </header>
      <main className="flex-1">
        <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none">
                  Your Intelligent <span className="text-indigo-600 dark:text-indigo-400">Campus Companion</span>
                </h1>
                <p className="mx-auto max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400">
                  Navigate college life with AI. Instant answers to syllabus queries, automated notices, and semantic document search.
                </p>
              </div>
              <div className="space-x-4">
                <Link to="/register">
                  <Button size="lg" className="h-12 px-8">
                    Join Nexora <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
        
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gray-50 dark:bg-gray-900">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="grid gap-8 sm:grid-cols-3">
              <div className="flex flex-col items-center space-y-3 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/50">
                  <Sparkles className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                </div>
                <h2 className="text-xl font-bold">AI RAG Engine</h2>
                <p className="text-gray-500 dark:text-gray-400">Ask anything about your courses. We'll search the actual documents and cite the exact page.</p>
              </div>
              <div className="flex flex-col items-center space-y-3 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/50">
                  <BookOpen className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                </div>
                <h2 className="text-xl font-bold">Smart Resources</h2>
                <p className="text-gray-500 dark:text-gray-400">Access verified PDFs, notices, and syllabus details, tailored precisely to your department.</p>
              </div>
              <div className="flex flex-col items-center space-y-3 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/50">
                  <Shield className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                </div>
                <h2 className="text-xl font-bold">Secure & Private</h2>
                <p className="text-gray-500 dark:text-gray-400">Enterprise-grade RBAC ensures students, faculty, and admins see only what they should.</p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
