import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, ThumbsUp, ThumbsDown, Copy } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { cn } from "../lib/utils";
import { API_URL } from "../config";

type Source = { document_title: string; page: number; relevance_score: number };
type Message = { id: number; role: string; content: string; sources?: Source[] };

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: "assistant", content: "Hello! I am your Nexora AI assistant. How can I help you with your college courses today?" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [expandedSources, setExpandedSources] = useState<Record<number, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e?: React.FormEvent, presetInput?: string) => {
    if (e) e.preventDefault();
    const query = presetInput || input;
    if (!query.trim() || isTyping) return;
    
    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: query }]);
    if (!presetInput) setInput("");
    setIsTyping(true);
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          query: query,
          conversation_id: conversationId
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const errorMsg = errData.detail || "Sorry, I encountered an error. Please try again.";
        throw new Error(errorMsg);
      }
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
    } catch (err: any) {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: "assistant", 
        content: err.message || "Sorry, I encountered an error. Please try again." 
      }]);
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

  const handleFeedback = async (messageId: number, isHelpful: boolean) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      await fetch(`${API_URL}/api/chat/${messageId}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ is_helpful: isHelpful })
      });
      alert(isHelpful ? "Thanks for your positive feedback!" : "Thanks for letting us know.");
    } catch (err) {
      console.error(err);
    }
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const toggleSources = (msgId: number) => {
    setExpandedSources(prev => ({...prev, [msgId]: !prev[msgId]}));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between pb-4">
        <h2 className="text-3xl font-bold tracking-tight">AI Assistant</h2>
      </div>
      
      <Card className="flex flex-col flex-1 overflow-hidden shadow-sm">
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
                  
                  {msg.role === "assistant" && msg.id !== 1 && (
                    <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700 flex flex-col gap-2">
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100" onClick={() => handleCopy(msg.content)} aria-label="Copy response">
                          <Copy className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-gray-500 hover:text-green-600 dark:text-gray-400" onClick={() => handleFeedback(msg.id, true)} aria-label="Helpful">
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-gray-500 hover:text-red-600 dark:text-gray-400" onClick={() => handleFeedback(msg.id, false)} aria-label="Not helpful">
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </Button>
                        {msg.sources && msg.sources.length > 0 && (
                           <button onClick={() => toggleSources(msg.id)} className="text-xs font-medium text-indigo-600 dark:text-indigo-400 ml-auto cursor-pointer hover:underline focus:outline-none">
                             {msg.sources.length} Source{msg.sources.length !== 1 ? 's' : ''}
                           </button>
                        )}
                      </div>
                      {expandedSources[msg.id] && msg.sources && (
                        <div className="mt-1 text-xs bg-gray-50 dark:bg-gray-900/50 p-3 rounded-lg border border-gray-200 dark:border-gray-800">
                           <ul className="list-disc pl-4 space-y-1">
                             {msg.sources.map((src, i) => (
                               <li key={i} className="text-gray-600 dark:text-gray-400">
                                 <span className="font-medium text-gray-900 dark:text-gray-200">{src.document_title}</span> (Page {src.page})
                               </li>
                             ))}
                           </ul>
                        </div>
                      )}
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
              placeholder="Ask anything about your courses... (Shift+Enter for new line)" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 input-field resize-none min-h-[44px] max-h-32 py-2.5 overflow-y-auto"
              rows={input.split('\n').length > 1 ? Math.min(input.split('\n').length, 4) : 1}
            />
            <Button type="submit" size="icon" disabled={isTyping || !input.trim()} className="h-11 w-11 shrink-0 rounded-xl">
              <Send className="h-5 w-5" />
              <span className="sr-only">Send message</span>
            </Button>
          </form>
          <div className="flex gap-2 mt-3 overflow-x-auto pb-1 scrollbar-hide">
            <span className="text-xs font-medium text-gray-500 py-1.5 whitespace-nowrap">Suggested:</span>
            <Button variant="outline" size="sm" className="h-7 text-xs rounded-full whitespace-nowrap bg-white dark:bg-gray-800" onClick={() => handleSend(undefined, "What is the attendance policy?")}>Attendance policy</Button>
            <Button variant="outline" size="sm" className="h-7 text-xs rounded-full whitespace-nowrap bg-white dark:bg-gray-800" onClick={() => handleSend(undefined, "When is the DB midterm?")}>DB midterm date</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
