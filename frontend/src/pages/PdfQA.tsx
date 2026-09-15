import React, { useState, useEffect, useRef } from "react";
import { Upload, FileText, Trash2, Send, Bot, User, MessageSquare } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { cn } from "../lib/utils";
import { API_URL } from "../config";

type Document = {
  id: number;
  title: string;
  status: string;
};

type Message = {
  id: number;
  role: string;
  content: string;
  sources?: any[];
};

export default function PdfQA() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`${API_URL}/api/documents/private`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle.trim()) return;
    
    setIsUploading(true);
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("title", uploadTitle);
    formData.append("file", uploadFile);

    try {
      const res = await fetch(`${API_URL}/api/documents/private`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });
      if (res.ok) {
        setUploadTitle("");
        setUploadFile(null);
        fetchDocuments();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`${API_URL}/api/documents/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        if (selectedDoc?.id === id) {
          setSelectedDoc(null);
          setMessages([]);
        }
        fetchDocuments();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectDoc = (doc: Document) => {
    setSelectedDoc(doc);
    setConversationId(null);
    setMessages([{ id: 1, role: "assistant", content: `I have loaded "${doc.title}". What would you like to know about it?` }]);
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || !selectedDoc || isTyping) return;
    
    const query = input;
    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: query }]);
    setInput("");
    setIsTyping(true);
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          query: query,
          conversation_id: conversationId,
          document_id: selectedDoc.id
        })
      });

      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      
      if (!conversationId && data.conversation_id) {
         setConversationId(data.conversation_id);
      }

      setMessages(prev => [...prev, { 
        id: data.message_id || Date.now(), 
        role: "assistant", 
        content: data.answer,
        sources: data.sources 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now(), role: "assistant", content: "Error communicating with server." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-8rem)]">
      {/* Sidebar: Document List & Upload */}
      <div className="w-full lg:w-1/3 flex flex-col gap-4">
        <h2 className="text-2xl font-bold">My PDFs</h2>
        
        <Card className="flex-shrink-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Upload New PDF</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpload} className="space-y-3">
              <Input 
                placeholder="Document Title" 
                value={uploadTitle} 
                onChange={(e) => setUploadTitle(e.target.value)} 
                required 
              />
              <Input 
                type="file" 
                accept="application/pdf" 
                onChange={(e) => e.target.files && setUploadFile(e.target.files[0])} 
                required 
                className="py-1.5 cursor-pointer"
              />
              <Button type="submit" disabled={isUploading || !uploadFile || !uploadTitle} className="w-full">
                <Upload className="h-4 w-4 mr-2" />
                {isUploading ? "Uploading..." : "Upload & Process"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="flex-1 overflow-y-auto space-y-2">
          {documents.map(doc => (
            <Card 
              key={doc.id} 
              className={cn("cursor-pointer transition-colors shadow-sm", selectedDoc?.id === doc.id ? "border-indigo-500 ring-1 ring-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/20" : "hover:bg-gray-50 dark:hover:bg-gray-800")}
              onClick={() => handleSelectDoc(doc)}
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3 overflow-hidden">
                  <FileText className="h-5 w-5 text-indigo-500 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium truncate text-sm">{doc.title}</h3>
                    <p className="text-xs text-gray-500 capitalize">{doc.status}</p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={(e) => handleDelete(e, doc.id)} className="h-8 w-8 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
          {documents.length === 0 && (
            <div className="text-center p-6 text-gray-500 text-sm border border-dashed rounded-xl dark:border-gray-800">
              No personal PDFs uploaded yet.
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {!selectedDoc ? (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500 border border-dashed border-gray-300 dark:border-gray-800 rounded-xl bg-gray-50/50 dark:bg-gray-900/50 shadow-sm">
            <MessageSquare className="h-12 w-12 mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Select a PDF to start chatting</h3>
            <p className="text-sm mt-1">Upload a document on the left and select it to isolate context.</p>
          </div>
        ) : (
          <Card className="flex flex-col flex-1 overflow-hidden shadow-sm h-full">
            <div className="p-4 border-b border-indigo-100 dark:border-indigo-900/30 bg-indigo-50/80 dark:bg-indigo-900/20 text-indigo-800 dark:text-indigo-300 font-medium text-sm flex items-center">
               <FileText className="h-4 w-4 mr-2" />
               Isolated Q&A Session: {selectedDoc.title}
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {messages.map((msg) => (
                <div key={msg.id} className={cn("flex w-full", msg.role === "user" ? "justify-end" : "justify-start")}>
                  <div className={cn("flex max-w-[85%] gap-3", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                    <div className={cn(
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-full shadow-sm",
                      msg.role === "user" ? "bg-indigo-600 text-white" : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
                    )}>
                      {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />}
                    </div>
                    <div className={cn(
                      "rounded-2xl px-5 py-3 shadow-sm",
                      msg.role === "user" ? "bg-indigo-600 text-white" : "bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"
                    )}>
                      {msg.role === "user" ? (
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      ) : (
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                      {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                         <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700 text-xs bg-gray-50/50 dark:bg-gray-900/30 rounded-md p-2">
                            <span className="font-medium text-gray-700 dark:text-gray-300 flex items-center mb-1">
                              <FileText className="h-3 w-3 mr-1" />
                              Sources:
                            </span>
                            <ul className="list-disc pl-4 space-y-1">
                              {msg.sources.map((src, i) => (
                                <li key={i} className="text-gray-600 dark:text-gray-400">
                                  Page {src.page}
                                </li>
                              ))}
                            </ul>
                         </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex w-full justify-start">
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                      <Bot className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div className="rounded-2xl px-5 py-4 bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center space-x-1.5 h-10">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"></div>
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0.15s" }}></div>
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0.3s" }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
              <form onSubmit={handleSend} className="flex gap-2 items-end">
                <textarea 
                  placeholder="Ask a question about this PDF... (Shift+Enter for new line)" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={selectedDoc.status !== "ready"}
                  className="flex-1 input-field resize-none min-h-[44px] max-h-32 py-2.5 overflow-y-auto"
                  rows={input.split('\n').length > 1 ? Math.min(input.split('\n').length, 4) : 1}
                />
                <Button type="submit" size="icon" disabled={isTyping || !input.trim() || selectedDoc.status !== "ready"} className="h-11 w-11 shrink-0 rounded-xl">
                  <Send className="h-5 w-5" />
                  <span className="sr-only">Send message</span>
                </Button>
              </form>
              {selectedDoc.status !== "ready" && (
                <p className="text-xs text-amber-600 dark:text-amber-500 mt-2 flex items-center bg-amber-50 dark:bg-amber-900/20 p-2 rounded-lg border border-amber-200 dark:border-amber-800/50">
                  <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse mr-2"></span>
                  Document is currently {selectedDoc.status}. Please wait until it's ready before asking questions.
                </p>
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
