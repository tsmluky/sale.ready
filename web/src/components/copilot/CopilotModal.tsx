import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../../services/api';
import { ChatMessage } from '../../types';
import { useAuth } from '../../context/AuthContext';
import { useCopilot, CopilotContextPayload } from '../../context/CopilotContext';
import { Link } from 'react-router-dom';
import { ShieldCheck, X, Eraser, Trash2, GripHorizontal, Settings } from 'lucide-react';

import toast from 'react-hot-toast';

export const CopilotModal: React.FC = () => {
    const { isOpen, closeCopilot, activeContext, clearContext } = useCopilot();
    const { userProfile } = useAuth();
    const plan = userProfile?.user.subscription_status || 'free';
    const isLocked = plan === 'free';

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const modalRef = useRef<HTMLDivElement>(null);

    // --- Dragging Logic ---
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragStartPos = useRef({ x: 0, y: 0 });

    // --- Resizing Logic ---
    const [size, setSize] = useState({ width: 384, height: 500 });
    const [isResizing, setIsResizing] = useState(false);
    const resizeStartPos = useRef({ x: 0, y: 0 });
    const startSize = useRef({ width: 0, height: 0 });

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
        dragStartPos.current = {
            x: e.clientX - position.x,
            y: e.clientY - position.y
        };
    };

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragStartPos.current.x,
                    y: e.clientY - dragStartPos.current.y
                });
            }
            if (isResizing) {
                const newWidth = Math.max(300, startSize.current.width + (e.clientX - resizeStartPos.current.x));
                const newHeight = Math.max(400, startSize.current.height + (e.clientY - resizeStartPos.current.y));
                setSize({ width: newWidth, height: newHeight });
            }
        };
        const handleMouseUp = () => {
            setIsDragging(false);
            setIsResizing(false);
        };

        if (isDragging || isResizing) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, isResizing]);

    const handleResizeMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsResizing(true);
        resizeStartPos.current = { x: e.clientX, y: e.clientY };
        startSize.current = { width: size.width, height: size.height };
    };

    // --- Click Outside to Close ---
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            // Only close if clicking outside the modal content AND dragging is not active
            if (isOpen && !isDragging && modalRef.current && !modalRef.current.contains(event.target as Node)) {
                closeCopilot();
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen, closeCopilot, isDragging]);


    // Track context processed to avoid loops
    const lastContextRef = useRef<CopilotContextPayload | null>(null);

    const initialMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        content: 'I am your TraderCopilot Advisor. How can I assist with your risk assessment?',
        type: 'text',
        timestamp: new Date().toISOString()
    };

    // Initial Welcome
    useEffect(() => {
        if (messages.length === 0) {
            setMessages([initialMessage]);
        }
    }, [messages.length]);

    // Clear Chat
    const handleClearChat = () => {
        setMessages([initialMessage]);
        toast.success("Conversation cleared");
    };

    // Auto-Send on Context Change
    useEffect(() => {
        if (isOpen && activeContext && activeContext !== lastContextRef.current) {
            lastContextRef.current = activeContext;

            let prompt = `Analyze current context.`;
            if (activeContext.token) {
                prompt = `Analyze ${activeContext.token} (${activeContext.timeframe || '1h'}).`;
            }
            if (activeContext.message) {
                prompt = activeContext.message;
            }

            handleSend(true, prompt);
        }
    }, [isOpen, activeContext]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSend = async (isAuto: boolean = false, customContent?: string) => {
        const text = customContent || input;
        if (!text.trim() && !isAuto) return;
        if (isLoading && !isAuto) return;

        const userMsg: ChatMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: text,
            type: 'text',
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMsg]);
        if (!isAuto) setInput('');
        setIsLoading(true);

        try {
            const apiContext = activeContext ? {
                token: activeContext.token,
                timeframe: activeContext.timeframe,
                signal_data: activeContext.signal
            } : undefined;

            const responseMsg = await api.sendAdvisorChat(
                [...messages, userMsg],
                apiContext
            );

            setMessages(prev => [...prev, responseMsg]);
        } catch (error) {
            console.error('Copilot error:', error);
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

    if (!isOpen) return null;

    // Calculate style for dragging
    // Default position: bottom-24 right-6. 
    // We start at (0,0) relative to that fixed position, adding user drag delta.
    const style: React.CSSProperties = {
        transform: `translate(${position.x}px, ${position.y}px)`,
        width: `${size.width}px`,
        height: `${size.height}px`,
        cursor: isDragging ? 'grabbing' : 'auto'
    };

    return (
        <div
            ref={modalRef}
            style={style}
            className="fixed bottom-24 right-6 z-[60] flex flex-col items-end pointer-events-auto transition-transform duration-75 will-change-transform"
        >
            {/* Container */}
            <div className="w-full h-full bg-[#0B1121] border border-gray-700/50 rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 fade-in duration-200 backdrop-blur-xl ring-1 ring-white/10">

                {/* Header (Draggable) */}
                <div
                    onMouseDown={handleMouseDown}
                    className="p-3 border-b border-white/5 bg-slate-900/80 sticky top-0 z-10 flex justify-between items-center backdrop-blur-md cursor-grab active:cursor-grabbing select-none"
                    title="Drag to move"
                >
                    <div className="flex items-center gap-3">
                        <div className="bg-indigo-500/10 p-2 rounded-lg border border-indigo-500/20 pointer-events-none">
                            <ShieldCheck className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div className="flex flex-col pointer-events-none">
                            <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                                TraderCopilot <GripHorizontal size={12} className="text-slate-600" />
                            </h3>
                            <div className="flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                <span className="text-[10px] font-medium text-emerald-500/80">Online</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-1" onMouseDown={(e) => e.stopPropagation()}>
                        {activeContext && (
                            <button onClick={clearContext} title="Clear Context" className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-white/5 transition-colors">
                                <Eraser size={16} />
                            </button>
                        )}
                        <button
                            onClick={handleClearChat}
                            title="Clear Chat History"
                            className="p-1.5 text-slate-400 hover:text-rose-400 rounded-md hover:bg-rose-500/10 transition-colors"
                        >
                            <Trash2 size={16} />
                        </button>
                        <Link
                            to="/settings"
                            onClick={closeCopilot}
                            title="Copilot Settings"
                            className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-white/5 transition-colors"
                        >
                            <Settings size={16} />
                        </Link>
                        <button
                            onClick={closeCopilot}
                            title="Close"
                            className="p-1.5 hover:bg-white/5 rounded-md text-slate-400 hover:text-white transition-all hover:rotate-90"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {/* Context Banner */}
                {activeContext && (
                    <div className="px-3 py-1.5 bg-indigo-500/10 border-b border-indigo-500/10 flex justify-between items-center">
                        <span className="text-xs text-indigo-300 font-medium truncate max-w-[200px]">
                            Context: {activeContext.token || 'General'} {activeContext.timeframe}
                        </span>
                    </div>
                )}

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-slate-950/30">
                    {messages.map((msg, idx) => {
                        const isUser = msg.role === 'user';
                        return (
                            <div key={msg.id || idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[85%] rounded-2xl p-3 text-sm shadow-sm ${isUser
                                    ? 'bg-indigo-600 text-white rounded-tr-none'
                                    : 'bg-slate-800/80 text-slate-200 rounded-tl-none border border-white/5'}`}>
                                    {isUser ? (
                                        <p className="whitespace-pre-wrap">{msg.content}</p>
                                    ) : (
                                        <div className="prose prose-invert prose-xs max-w-none">
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
                            <div className="bg-slate-800/50 rounded-2xl rounded-tl-none p-3 border border-white/5">
                                <div className="flex gap-1">
                                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-100"></span>
                                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-200"></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-3 bg-slate-900 border-t border-white/5">
                    {isLocked ? (
                        <div className="text-center py-2">
                            <p className="text-xs text-slate-400 mb-2">Upgrade to Chat</p>
                            <Link to="/pricing" className="text-xs font-bold text-indigo-400 hover:text-indigo-300">View Plans</Link>
                        </div>
                    ) : (
                        <div className="flex gap-2">
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyPress}
                                placeholder={activeContext?.token ? `Ask about ${activeContext.token}...` : "Ask anything..."}
                                className="flex-1 bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-white/10 focus:border-indigo-500 focus:outline-none placeholder-slate-500"
                            />
                            <button
                                onClick={() => handleSend()}
                                disabled={isLoading || !input.trim()}
                                className="p-2 bg-indigo-600 rounded-lg text-white disabled:opacity-50 hover:bg-indigo-500 transition-colors"
                            >
                                ➤
                            </button>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-3 py-1 bg-slate-950 text-center border-t border-white/5 relative">
                    <span className="text-[10px] text-slate-600">AI output. Not financial advice.</span>

                    {/* Resize Handle */}
                    <div
                        onMouseDown={handleResizeMouseDown}
                        className="absolute bottom-1 right-1 cursor-se-resize w-4 h-4 text-slate-500 hover:text-white transition-colors opacity-50 hover:opacity-100 p-0.5"
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15v6" />
                            <path d="M15 21h6" />
                            <path d="M21 9v2" />
                            <path d="M9 21h2" />
                        </svg>
                    </div>
                </div>

            </div>
        </div>
    );
};
