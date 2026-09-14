import React, { useState } from "react";
import { Search as SearchIcon, Database, Key } from "lucide-react";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { cn } from "../lib/utils";
import { API_URL } from "../config";

type SearchResult = {
  id: number;
  chunk_text: string;
  document_title: string;
  page_number: number;
  document_id: number;
  relevance_score: number;
  metadata: any;
};

export default function Search() {
  const [query, setQuery] = useState("");
  const [searchMode, setSearchMode] = useState<"semantic" | "keyword">("semantic");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    const token = localStorage.getItem("token");
    
    try {
      const res = await fetch(`${API_URL}/api/search?query=${encodeURIComponent(query)}&search_mode=${searchMode}`, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
      });
      
      if (res.ok) {
        const data = await res.json();
        setResults(data.results);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6 max-w-5xl mx-auto w-full">
      <div className="flex flex-col items-center text-center space-y-4 mb-8 mt-4">
        <h2 className="text-4xl font-bold tracking-tight">Global Search</h2>
        <p className="text-gray-500">Discover knowledge across all college documents.</p>
        
        <form onSubmit={handleSearch} className="w-full max-w-2xl relative flex items-center mt-4">
          <SearchIcon className="absolute left-3 h-5 w-5 text-gray-400" />
          <Input 
            className="h-14 pl-10 pr-24 rounded-full text-lg shadow-sm" 
            placeholder="Search for 'machine learning syllabus'..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Button type="submit" disabled={isSearching} className="absolute right-1.5 h-11 rounded-full px-6">
            {isSearching ? "Searching..." : "Search"}
          </Button>
        </form>

        <div className="flex items-center gap-2 mt-4 bg-gray-100 dark:bg-gray-800 p-1 rounded-full">
          <button
            type="button"
            onClick={() => setSearchMode("semantic")}
            className={cn(
              "px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-2",
              searchMode === "semantic" ? "bg-white dark:bg-gray-700 shadow text-indigo-600 dark:text-indigo-400" : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            )}
          >
            <Database className="w-4 h-4" /> Semantic (AI)
          </button>
          <button
            type="button"
            onClick={() => setSearchMode("keyword")}
            className={cn(
              "px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-2",
              searchMode === "keyword" ? "bg-white dark:bg-gray-700 shadow text-indigo-600 dark:text-indigo-400" : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            )}
          >
            <Key className="w-4 h-4" /> Keyword Match
          </button>
        </div>
      </div>

      <div className="space-y-4 mt-8">
        {results.length > 0 ? (
          <div>
            <h3 className="text-lg font-semibold mb-4">Found {results.length} results</h3>
            <div className="grid gap-4">
              {results.map((result, idx) => (
                <Card key={idx} className="overflow-hidden hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-lg text-indigo-600 dark:text-indigo-400">
                        {result.document_title}
                      </h4>
                      {searchMode === "semantic" && (
                        <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                          Score: {(1 - result.relevance_score).toFixed(2)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mb-3">Page {result.page_number}</p>
                    <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed line-clamp-3">
                      "...{result.chunk_text}..."
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          !isSearching && query && (
            <div className="text-center py-12 text-gray-500">
              No results found. Try adjusting your search mode or terms.
            </div>
          )
        )}
      </div>
    </div>
  );
}
