import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, X, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "./ui/button";
import { cn } from "../lib/utils";
import { API_URL } from "../config";

type Message = { id: number; role: string; content: string; };

interface AskNexoraProps {
  isOpen: boolean;
  onClose: () => void;
  contextType: string;
  contextId?: string;
  contextTitle: string;
  suggestions: string[];
}

export default function AskNexoraContextual({ isOpen, onClose, contextType, contextId, contextTitle, suggestions }: AskNexoraProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        id: 1, 
        role: "assistant", 
        content: `Hi! I'm Nexora. Ask me anything about ${contextTitle}.`
      }]);
    }
  }, [isOpen, contextTitle, messages.length]);

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
      const res = await fetch(`${API_URL}/api/chat/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          query: query,
          conversation_id: conversationId,
          context_type: contextType,
          context_id: contextId
        })
      });

      if (!res.ok) throw new Error("Failed to get response");
      const data = await res.json();
      
      if (!conversationId && data.conversation_id) {
         setConversationId(data.conversation_id);
      }

      setMessages(prev => [...prev, { 
        id: data.message_id || Date.now(), 
        role: "assistant", 
        content: data.answer
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: "assistant", 
        content: "Sorry, I encountered an error. Please try again." 
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full md:w-[450px] bg-white dark:bg-gray-900 shadow-2xl flex flex-col border-l border-gray-200 dark:border-gray-800 transition-transform transform">
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800 bg-indigo-50/50 dark:bg-indigo-900/10">
        <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-400">
          <Sparkles className="h-5 w-5" />
          <div>
            <h3 className="font-semibold text-lg leading-tight">Ask Nexora</h3>
            <p className="text-xs text-indigo-600/80 dark:text-indigo-400/80">Your Intelligent Campus Companion</p>
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="rounded-full hover:bg-indigo-100 dark:hover:bg-gray-800">
          <X className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className={cn("flex w-full", msg.role === "user" ? "justify-end" : "justify-start")}>
            <div className={cn("flex max-w-[90%] gap-3", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
              <div className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full shadow-sm",
                msg.role === "user" ? "bg-indigo-600 text-white" : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
              )}>
                {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />}
              </div>
              <div className={cn(
                "rounded-2xl px-4 py-2.5 shadow-sm text-sm",
                msg.role === "user" ? "bg-indigo-600 text-white" : "bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"
              )}>
                {msg.role === "user" ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
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
                <Bot className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div className="rounded-2xl px-4 py-3 bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center space-x-1.5 h-10">
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
        <div className="flex flex-wrap gap-2 mb-3">
          {suggestions.map((sug, i) => (
            <Button key={i} variant="outline" size="sm" className="h-7 text-xs rounded-full whitespace-nowrap bg-white dark:bg-gray-800 border-indigo-100 text-indigo-700 hover:bg-indigo-50 dark:border-gray-700 dark:text-indigo-300 dark:hover:bg-gray-800" onClick={() => handleSend(undefined, sug)}>
              {sug}
            </Button>
          ))}
        </div>
        <form onSubmit={handleSend} className="flex gap-2 items-end">
          <textarea 
            placeholder="Type your question..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 input-field resize-none min-h-[44px] max-h-32 py-2.5 overflow-y-auto rounded-xl border-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
            rows={input.split('\n').length > 1 ? Math.min(input.split('\n').length, 4) : 1}
          />
          <Button type="submit" size="icon" disabled={isTyping || !input.trim()} className="h-11 w-11 shrink-0 rounded-xl bg-indigo-600 hover:bg-indigo-700">
            <Send className="h-5 w-5" />
          </Button>
        </form>
      </div>
    </div>
  );
}
