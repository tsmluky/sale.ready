import React, { useEffect, useState, useRef } from 'react';
import { ExternalLink, ChevronRight, ChevronLeft } from 'lucide-react';
import { newsService, NewsItem } from '../../services/newsService';
import { cn } from '../../lib/utils';

export const NewsCarousel: React.FC = () => {
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPaused, setIsPaused] = useState(false);

    // Responsive Logic
    const [itemsPerPage, setItemsPerPage] = useState(3);

    // Swipe Logic
    const touchStartX = useRef<number | null>(null);
    const touchEndX = useRef<number | null>(null);
    const minSwipeDistance = 50;
    const isSwiping = useRef(false);

    const AUTO_PLAY_INTERVAL = 60000; // 60s

    useEffect(() => {
        const handleResize = () => {
            setItemsPerPage(window.innerWidth < 768 ? 1 : 3);
        };
        handleResize(); // Init
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        const fetchNews = async () => {
            try {
                const items = await newsService.getLatestNews();
                setNews(items);
            } catch (err) {
                console.error("Failed to load news", err);
            } finally {
                setLoading(false);
            }
        };

        fetchNews();
        // Refresh every 2 minutes
        const interval = setInterval(fetchNews, 2 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    const totalPages = Math.ceil(news.length / itemsPerPage);

    // Reset index if resizing changes total pages
    useEffect(() => {
        if (currentIndex >= totalPages && totalPages > 0) {
            setCurrentIndex(totalPages - 1);
        }
    }, [itemsPerPage, totalPages]);

    const nextSlide = () => {
        setCurrentIndex((prev) => (prev + 1) % totalPages);
    };

    const prevSlide = () => {
        setCurrentIndex((prev) => (prev - 1 + totalPages) % totalPages);
    };

    // Auto Play
    useEffect(() => {
        if (totalPages <= 1 || isPaused) return;
        const interval = setInterval(nextSlide, AUTO_PLAY_INTERVAL);
        return () => clearInterval(interval);
    }, [totalPages, isPaused]);

    // Swipe Handlers
    const onTouchStart = (e: React.TouchEvent | React.MouseEvent) => {
        setIsPaused(true);
        touchStartX.current = 'touches' in e ? e.touches[0].clientX : (e as React.MouseEvent).clientX;
        isSwiping.current = false;
    };

    const onTouchMove = (e: React.TouchEvent | React.MouseEvent) => {
        if (!touchStartX.current) return;
        touchEndX.current = 'touches' in e ? e.touches[0].clientX : (e as React.MouseEvent).clientX;

        // Detect if it's a drag/swipe vs just a click
        if (Math.abs(touchStartX.current - touchEndX.current) > 10) {
            isSwiping.current = true;
        }
    };

    const onTouchEnd = () => {
        setIsPaused(false);
        if (!touchStartX.current || !touchEndX.current) return;

        const distance = touchStartX.current - touchEndX.current;
        const isLeftSwipe = distance > minSwipeDistance;
        const isRightSwipe = distance < -minSwipeDistance;

        if (isLeftSwipe) {
            nextSlide();
        } else if (isRightSwipe) {
            prevSlide();
        }

        // Reset
        touchStartX.current = null;
        touchEndX.current = null;
        // Note: isSwiping remains true briefly to block click if needed, 
        // but since click handler runs after mouseup, we might need a small timeout or capture handling.
        // Actually, for React onClick, simple ref check works if we process events right.
        setTimeout(() => isSwiping.current = false, 100);
    };

    // Split news into pages based on dynamic itemsPerPage
    const pages = [];
    for (let i = 0; i < news.length; i += itemsPerPage) {
        pages.push(news.slice(i, i + itemsPerPage));
    }

    if (!loading && news.length === 0) return null;

    return (
        <div
            className="w-full mt-2 animate-in fade-in duration-700 select-none relative group/slider"
            onMouseEnter={() => setIsPaused(true)}
            onMouseLeave={() => setIsPaused(false)}
            // Bind unified touch/mouse handlers to container
            onTouchStart={onTouchStart}
            onTouchMove={onTouchMove}
            onTouchEnd={onTouchEnd}
            onMouseDown={onTouchStart}
            onMouseMove={onTouchMove}
            onMouseUp={onTouchEnd}
        >
            {/* Main Content Area */}
            <div className="overflow-hidden bg-[#0A0E17]/30 rounded-2xl border border-white/5 p-1 backdrop-blur-sm cursor-grab active:cursor-grabbing">
                <div
                    className="flex transition-transform duration-500 ease-in-out will-change-transform"
                    style={{ transform: `translateX(-${currentIndex * 100}%)` }}
                >
                    {loading ? (
                        <div className="w-full shrink-0 grid grid-cols-1 md:grid-cols-3 gap-6">
                            {Array(itemsPerPage).fill(0).map((_, i) => (
                                <div key={i} className="h-[140px] rounded-2xl bg-white/5 animate-pulse border border-white/5" />
                            ))}
                        </div>
                    ) : (
                        pages.map((pageItems, pageIdx) => (
                            // Grid changes based on itemsPerPage logic, but we use w-full.
                            // If itemsPerPage is 1, grid-cols-1. If 3, grid-cols-1 md:grid-cols-3.
                            // But cleaner: just use dynamic grid class or style? 
                            // Tailwinds 'md:grid-cols-3' handles it automatically IF the pageItems has 3 items.
                            // But if we slice 1 item for mobile, the grid will naturally have 1 item.
                            // We just need to make sure the container grid definition allows it.
                            <div
                                key={pageIdx}
                                className={cn(
                                    "w-full shrink-0 grid gap-4 md:gap-6 px-1 py-1",
                                    itemsPerPage === 1 ? "grid-cols-1" : "grid-cols-1 md:grid-cols-3"
                                )}
                            >
                                {pageItems.map((item, idx) => (
                                    <a
                                        key={`${item.id}-${idx}`}
                                        href={item.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        draggable="false"
                                        onDragStart={(e) => e.preventDefault()}
                                        onClick={(e) => {
                                            if (isSwiping.current) {
                                                e.preventDefault();
                                                e.stopPropagation();
                                            }
                                        }}
                                        className="group relative flex flex-col justify-between p-4 rounded-xl bg-[#0B1121] border border-white/5 hover:border-brand-500/40 transition-all duration-300 h-[140px] hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] overflow-hidden"
                                    >
                                        {/* Decorative Background Gradient */}
                                        <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-2xl -mr-10 -mt-10 transition-opacity group-hover:bg-brand-500/10 pointer-events-none" />

                                        <div className="relative z-10 flex flex-col h-full pointer-events-none">
                                            <div className="flex items-center justify-between gap-3 mb-2">
                                                <div className="flex items-center gap-2">
                                                    <span className={cn(
                                                        "w-1.5 h-1.5 rounded-full",
                                                        idx === 0 && pageIdx === 0 ? "bg-emerald-500 animate-pulse" : "bg-slate-600"
                                                    )} />
                                                    <h4 className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                                                        {item.currencies && item.currencies[0] ? item.currencies[0].code : 'NEWS'}
                                                    </h4>
                                                </div>
                                                <ExternalLink size={10} className="text-slate-700 group-hover:text-brand-400 transition-colors" />
                                            </div>

                                            <p className="text-sm font-medium text-slate-200 leading-snug line-clamp-2 group-hover:text-white transition-colors mb-auto">
                                                {item.title}
                                            </p>

                                            <div className="mt-auto pt-3 border-t border-white/5 flex items-center justify-between">
                                                <div className="flex items-center gap-1.5 overflow-hidden">
                                                    {item.currencies?.slice(0, 2).map((tag, i) => (
                                                        <span key={i} className={cn(
                                                            "text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider border",
                                                            tag.code === 'BTC' ? "bg-[#f7931a]/10 text-[#f7931a] border-[#f7931a]/20" :
                                                                tag.code === 'ETH' ? "bg-[#627eea]/10 text-[#627eea] border-[#627eea]/20" :
                                                                    tag.code === 'SOL' ? "bg-[#14f195]/10 text-[#14f195] border-[#14f195]/20" :
                                                                        tag.code === 'USDT' || tag.code === 'MKT' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                                                                            tag.code === 'XRP' ? "bg-white/10 text-slate-300 border-white/20" :
                                                                                "bg-brand-500/10 text-brand-400 border-brand-500/20"
                                                        )}>
                                                            {tag.code}
                                                        </span>
                                                    ))}
                                                </div>

                                                <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1.5 shrink-0">
                                                    {(() => {
                                                        const now = new Date();
                                                        const date = new Date(item.published_at);
                                                        if (isNaN(date.getTime())) return 'LIVE';
                                                        const diff = Math.floor((now.getTime() - date.getTime()) / 60000);
                                                        if (diff < 1) return 'LIVE';
                                                        return `${Math.floor(diff / 60)}h ${diff % 60}m`;
                                                    })()}
                                                </span>
                                            </div>
                                        </div>
                                    </a>
                                ))}
                                {/* Fill empty slots */}
                                {pageItems.length < itemsPerPage && Array(itemsPerPage - pageItems.length).fill(0).map((_, i) => (
                                    <div key={`empty-${i}`} className="hidden md:block" />
                                ))}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Hover Navigation Arrows (Overlay) - Hidden on Mobile */}
            <button
                onClick={(e) => { e.preventDefault(); prevSlide(); }}
                className="hidden md:flex absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-[#020617] to-transparent z-20 items-center justify-start pl-2 opacity-0 group-hover/slider:opacity-100 transition-opacity duration-300 pointer-events-none group-hover/slider:pointer-events-auto cursor-pointer"
            >
                <div className="p-2 rounded-full bg-slate-800/80 text-slate-200 hover:bg-brand-500 hover:text-white transition-all shadow-lg border border-white/10 transform hover:scale-110">
                    <ChevronLeft size={20} />
                </div>
            </button>

            <button
                onClick={(e) => { e.preventDefault(); nextSlide(); }}
                className="hidden md:flex absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-[#020617] to-transparent z-20 items-center justify-end pr-2 opacity-0 group-hover/slider:opacity-100 transition-opacity duration-300 pointer-events-none group-hover/slider:pointer-events-auto cursor-pointer"
            >
                <div className="p-2 rounded-full bg-slate-800/80 text-slate-200 hover:bg-brand-500 hover:text-white transition-all shadow-lg border border-white/10 transform hover:scale-110">
                    <ChevronRight size={20} />
                </div>
            </button>

            {/* Pagination Indicators (Bottom Right) */}
            <div className="absolute bottom-[-12px] right-2 flex items-center gap-1.5 z-20">
                {pages.map((_, i) => (
                    <button
                        key={i}
                        onClick={() => setCurrentIndex(i)}
                        className={cn(
                            "h-1 rounded-full transition-all duration-300",
                            currentIndex === i ? "w-6 bg-brand-500" : "w-1.5 bg-slate-700 hover:bg-slate-500"
                        )}
                    />
                ))}
            </div>
        </div>
    );
};
