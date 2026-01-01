import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';
import { ChatMessage } from '../types';

interface AdvisorChatProps {
  currentToken?: string;
  currentTimeframe?: string;
  initialContext?: any; // New: For passing full signal context
  embedded?: boolean;   // New: Render without floating button
}

import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { ShieldCheck, X, Send } from 'lucide-react';

export const AdvisorChat: React.FC<AdvisorChatProps> = ({ currentToken, currentTimeframe, initialContext, embedded = false }) => {
  const { userProfile } = useAuth();
  const plan = userProfile?.user.subscription_status || 'free';
  const isLocked = plan === 'free';

  // If embedded, default to open. Else default to closed.
  const [isOpen, setIsOpen] = useState(embedded);

  // Initial welcome message from assistant
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize Check
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    if (initialContext) {
      // Auto-trigger analysis
      handleSend(initialContext, true);
    } else {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: 'How can I assist you with risk assessment today?',
        type: 'text',
        timestamp: new Date().toISOString()
      }]);
    }
  }, [initialContext]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  // Listen for 'open-advisor-chat' events
  useEffect(() => {
    if (embedded) return;
    const handleOpenEvent = (e: CustomEvent) => {
      setIsOpen(true);
      // Auto-analyze if context is provided
      if (e.detail) {
        const { token, direction, entry, timeframe } = e.detail;
        if (token) {
          // Reset messages if it's a new token or context switch?
          // For now, simpler is to just append analysis relative to new context.

          // Construct auto-context object
          const ctx = { token, timeframe: timeframe || '4h' }; // default to 4h if missing

          // Only trigger if we haven't just triggered for this exact context (debounce/dedupe?)
          // Or just trust the user click.

          // Trigger hidden auto-send
          handleSend(ctx, true, `Analyze ${token} ${direction} setup at ${entry}. Risk assessment?`);
        }
      }
    };

    window.addEventListener('open-advisor-chat', handleOpenEvent as EventListener);
    return () => window.removeEventListener('open-advisor-chat', handleOpenEvent as EventListener);
  }, [embedded]);

  const handleSend = async (overrideContext?: any, isInitialAutoSend: boolean = false, customPrompt?: string) => {
    // Allow empty input if it's the initial auto-send
    if (!isInitialAutoSend && (!input.trim() || isLoading)) return;

    let userMsg: ChatMessage;

    if (isInitialAutoSend) {
      // System / Implicit Prompt
      userMsg = {
        id: Date.now().toString(),
        role: 'user',
        content: customPrompt || `Analyze the following trade setup: ${overrideContext?.token}.`,
        type: 'text',
        timestamp: new Date().toISOString(),
      };
      // We ADD this to UI so user sees "Agent" is responding to *something*
      setMessages(prev => [...prev, userMsg]);
    } else {
      userMsg = {
        id: Date.now().toString(),
        role: 'user',
        content: input,
        type: 'text',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMsg]);
      setInput('');
    }

    setIsLoading(true);

    try {
      const context = overrideContext || {
        token: currentToken,
        timeframe: currentTimeframe
      };

      // Use the dedicated service method
      const responseMsg = await api.sendAdvisorChat(
        isInitialAutoSend ? [userMsg] : [...messages, userMsg],
        context
      );

      setMessages(prev => [...prev, responseMsg]);

    } catch (error) {
      console.error('Advisor chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: '❌ Connection error. Please check system logs.',
        type: 'text',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // --- RENDER HELPERS ---

  // 1. Embedded Mode Render
  if (embedded) {
    return (
      <div className="flex flex-col h-full bg-[#0B1121]">
        {/* Messages Area */}
        {/* Messages Area - Refined */}
        <div className="flex-1 overflow-y-auto w-full p-4 space-y-4 custom-scrollbar">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id || idx}
                className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-1 duration-300`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl p-4 text-sm shadow-sm backdrop-blur-md border ${isUser
                    ? 'bg-gradient-to-br from-brand-600/90 to-indigo-600/90 text-white rounded-tr-sm border-white/10 shadow-indigo-500/20'
                    : 'bg-[#1e293b]/60 text-slate-200 rounded-tl-sm border-white/5 shadow-black/20'
                    }`}
                >
                  {isUser ? (
                    <p className="whitespace-pre-wrap leading-relaxed tracking-wide font-medium">{msg.content}</p>
                  ) : (
                    <div className="prose prose-invert prose-sm max-w-none [&>p]:leading-relaxed [&>ul]:list-disc [&>ul]:pl-4 [&>h3]:text-brand-400 [&>h3]:font-bold [&>strong]:text-brand-300">
                      {/* @ts-ignore */}
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-[#1e293b]/60 text-slate-400 rounded-2xl p-4 border border-white/5 rounded-tl-sm flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area - Seamless */}
        <div className="p-4 bg-[#020617]/80 border-t border-white/5 backdrop-blur-xl pb-8">
          <div className="flex gap-3 items-end bg-white/5 rounded-xl border border-white/5 p-2 focus-within:border-brand-500/30 focus-within:bg-white/10 transition-all">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask Copilot..."
              className="flex-1 bg-transparent text-white border-none p-2 text-sm focus:ring-0 resize-none h-10 max-h-32 py-2.5 placeholder:text-slate-500 leading-relaxed scrollbar-none [&::-webkit-scrollbar]:hidden w-full focus:outline-none"
              rows={1}
              style={{ minHeight: '40px', msOverflowStyle: 'none', scrollbarWidth: 'none' }}
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className={`p-2 rounded-lg bg-brand-500 text-white hover:bg-brand-400 transition-all shadow-lg hover:shadow-brand-500/25 shrink-0 mb-0.5 ${(isLoading || !input.trim()) ? 'opacity-50 cursor-not-allowed grayscale' : ''
                }`}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 2. Floating Mode Render (Original)
  return (
    <div className="fixed bottom-6 right-6 z-[60] flex flex-col items-end pointer-events-none">
      {/* Chat Window - Enable pointer events for children */}
      {isOpen && (
        <div className="mb-4 w-80 md:w-96 h-[450px] bg-[#0B1121] border border-gray-700 rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-10 duration-300 pointer-events-auto">
          {/* Header */}
          <div className="p-4 border-b border-slate-800 bg-slate-900/95 sticky top-0 z-10 flex justify-between items-center backdrop-blur-md">
            <div className="flex items-center gap-2">
              <div className="bg-indigo-500/10 p-2 rounded-lg border border-indigo-500/20">
                <ShieldCheck className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h3 className="font-bold text-slate-200 text-sm">TraderCopilot Advisor</h3>
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-[10px] uppercase font-bold text-emerald-500/80 tracking-wider">Secure Channel</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-all hover:rotate-90"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar bg-slate-900/50">
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id || idx}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg p-3 text-sm shadow-md ${isUser
                      ? 'bg-blue-600 text-white rounded-tr-none'
                      : 'bg-gray-800 text-gray-200 rounded-tl-none border border-gray-700'
                      }`}
                  >
                    {isUser ? (
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    ) : (
                      <div className="prose prose-invert prose-sm max-w-none [&>ul]:list-disc [&>ul]:pl-4 [&>ol]:list-decimal [&>ol]:pl-4 [&>h3]:text-indigo-400 [&>h3]:font-bold [&>strong]:text-indigo-300">
                        {/* @ts-ignore */}
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-400 rounded-lg p-3 text-sm border border-gray-700 animate-pulse">
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce delay-0"></span>
                    <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce delay-100"></span>
                    <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce delay-200"></span>
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* DISCLAIMER FOOTER */}
          <div className="px-4 py-2 bg-slate-950/50 border-t border-slate-900 text-center">
            <p className="text-[10px] text-slate-600 font-medium">
              TraderCopilot Advisor provides technical analysis for educational purposes only. Not financial advice.
            </p>
          </div>

          {/* Input Area */}
          <div className="p-3 bg-gray-800/80 border-t border-gray-700 backdrop-blur-sm">
            {isLocked ? (
              <div className="text-center py-2 h-full flex flex-col justify-center">
                <p className="text-sm text-slate-400 mb-2">Advisor Chat is available on Paid Plans.</p>
                <Link to="/membership" className="inline-block px-4 py-1.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white text-xs font-bold rounded-full shadow-lg hover:scale-105 transition-transform">
                  Upgrade to Unlock
                </Link>
              </div>
            ) : (
              <div className="flex gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={currentToken ? `Ask about ${currentToken}...` : "Analyze risk profile..."}
                  className="flex-1 bg-[#1E293B] text-white border border-gray-600 rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 resize-none h-10 py-2.5 scrollbar-none"
                  rows={1}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={isLoading || !input.trim()}
                  className={`px-3 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-500 transition-colors shadow-lg ${(isLoading || !input.trim()) ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                >
                  ➤
                </button>
              </div>
            )}
          </div>
        </div>
      )}


    </div>
  );
};
