import React, { useMemo } from 'react';
import { Bot, Sparkles, Globe, Activity, Crosshair, Lightbulb, ListChecks } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface ProAnalysisViewerProps {
  raw: string;
  token: string;
}

export function ProAnalysisViewer({ raw, token }: ProAnalysisViewerProps) {

  const sections = useMemo(() => {
    if (!raw) return null;

    // Parser for the #TAG# format
    const parse = (tag: string) => {
      const regex = new RegExp(`#${tag}#([\\s\\S]*?)(?=#|$)`, 'i');
      const match = raw.match(regex);
      return match ? match[1].trim() : null;
    };

    return {
      context: parse('CTXT'),
      technical: parse('TA'),
      plan: parse('PLAN'),
      insight: parse('INSIGHT'),
      params: parse('PARAMS'),
      // Fallback: if no tags found, show full raw
      fallback: raw.includes('#ANALYSIS_START') ? null : raw
    };
  }, [raw]);

  if (!raw) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-500 opacity-50 animate-pulse">
        <Sparkles size={48} className="mb-4 text-slate-600" />
        <p className="font-mono text-sm">Initializing Neural Net...</p>
      </div>
    );
  }

  // Fallback for non-tagged responses (e.g. errors or legacy)
  if (sections?.fallback) {
    return (
      <div className="glass-card rounded-2xl p-6 lg:p-8 animate-in fade-in slide-in-from-bottom-5 duration-700">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Bot size={20} className="text-brand-400" /> Analysis Report
        </h3>
        <div className="prose prose-invert max-w-none text-slate-300">
          <ReactMarkdown>{sections.fallback}</ReactMarkdown>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-5 duration-700">

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
          <Bot size={20} className="text-white" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            Institutional Report
            <span className="px-2 py-0.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-[10px] text-brand-300 font-mono uppercase">PRO Agent</span>
          </h3>
          <p className="text-slate-400 text-xs font-mono tracking-wide">GENERATED FOR {token}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Context Column */}
        <div className="space-y-6">
          {sections?.context && (
            <Card className="bg-black/20 border-white/10 overflow-hidden">
              <CardHeader className="bg-white/5 pb-3">
                <CardTitle className="text-sm font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                  <Globe size={16} className="text-blue-400" /> Market Context
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-slate-300 text-sm leading-relaxed">
                <ReactMarkdown>{sections.context}</ReactMarkdown>
              </CardContent>
            </Card>
          )}

          {sections?.insight && (
            <Card className="bg-gradient-to-br from-brand-900/10 to-indigo-900/10 border-brand-500/20">
              <CardHeader className="pb-3 border-b border-brand-500/10">
                <CardTitle className="text-sm font-bold text-brand-300 flex items-center gap-2 uppercase tracking-wider">
                  <Lightbulb size={16} className="text-brand-400" /> Key Insight
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-brand-100 text-sm italic font-medium leading-relaxed">
                <ReactMarkdown>{sections.insight}</ReactMarkdown>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Technical Column */}
        <div className="space-y-6">
          {sections?.technical && (
            <Card className="bg-black/20 border-white/10 h-full">
              <CardHeader className="bg-white/5 pb-3">
                <CardTitle className="text-sm font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                  <Activity size={16} className="text-emerald-400" /> Technical Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-slate-300 text-sm leading-relaxed space-y-2">
                <ReactMarkdown>{sections.technical}</ReactMarkdown>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Execution Plan (Full Width) */}
      {sections?.plan && (
        <Card className="bg-black/40 border-white/10">
          <CardHeader className="pb-3 border-b border-white/5">
            <CardTitle className="text-sm font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
              <Crosshair size={16} className="text-rose-400" /> Execution Plan
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 text-slate-300 text-sm leading-relaxed grid md:grid-cols-2 gap-8">
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{sections.plan}</ReactMarkdown>
            </div>

            {/* Render Params if available */}
            {sections.params && (
              <div className="bg-white/5 rounded-xl p-4 border border-white/10 font-mono text-xs">
                <div className="text-slate-500 mb-2 uppercase font-bold tracking-widest">Confirmed Levels</div>
                <div className="whitespace-pre-wrap text-slate-300">
                  {sections.params}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

    </div>
  );
}
