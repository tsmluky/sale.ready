import React, { useState, useRef, useEffect } from 'react';
import { Search, ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';

interface TokenSelectorProps {
    value: string;
    onChange: (value: string) => void;
    tokens: string[];
}

export const TokenSelector: React.FC<TokenSelectorProps> = ({ value, onChange, tokens }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState('');
    const containerRef = useRef<HTMLDivElement>(null);

    // Filter tokens
    const filteredTokens = tokens.filter(t =>
        t.toLowerCase().includes(search.toLowerCase())
    );

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Focus input on open
    const inputRef = useRef<HTMLInputElement>(null);
    useEffect(() => {
        if (isOpen && inputRef.current) {
            // Small timeout to allow render
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    }, [isOpen]);

    return (
        <div className="relative w-full" ref={containerRef}>
            <div
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center justify-between w-full h-11 px-3 bg-black/20 border border-white/10 rounded-md cursor-pointer hover:bg-white/5 transition-colors text-white font-bold text-lg"
            >
                <div className="flex items-center gap-2">
                    {/* Optional: Add token icon here if we had them */}
                    <span>{value || 'Select Token'}</span>
                </div>
                <ChevronDown size={16} className={cn("text-slate-400 transition-transform", isOpen && "rotate-180")} />
            </div>

            {isOpen && (
                <div className="absolute top-[calc(100%+4px)] left-0 w-full z-50 bg-[#0f172a] border border-white/10 rounded-lg shadow-2xl shadow-black overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                    <div className="p-2 border-b border-white/5 sticky top-0 bg-[#0f172a] z-10">
                        <div className="relative">
                            <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                            <Input
                                ref={inputRef}
                                placeholder="Search ticker..."
                                className="pl-8 h-9 text-sm bg-white/5 border-white/10 focus:ring-brand-500/50"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                            />
                        </div>
                    </div>

                    <div className="max-h-[250px] overflow-y-auto p-1 custom-scrollbar">
                        {filteredTokens.length === 0 ? (
                            <div className="p-4 text-center text-sm text-slate-500 italic">
                                No tokens found.
                            </div>
                        ) : (
                            filteredTokens.map((token) => (
                                <div
                                    key={token}
                                    onClick={() => {
                                        onChange(token);
                                        setIsOpen(false);
                                        setSearch('');
                                    }}
                                    className={cn(
                                        "flex items-center justify-between px-3 py-2.5 rounded-md cursor-pointer transition-colors text-sm font-bold",
                                        token === value
                                            ? "bg-brand-500/20 text-brand-400"
                                            : "text-slate-300 hover:bg-white/5 hover:text-white"
                                    )}
                                >
                                    <span>{token}</span>
                                    {token === value && <Check size={14} className="text-brand-500" />}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
