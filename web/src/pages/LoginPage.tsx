import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Activity,
  Lock,
  Mail,
  ArrowRight,
  Loader2,
  TrendingUp,
  ShieldCheck,
  Zap,
  BarChart2,
  Cpu,
  CheckCircle2,
  ChevronRight
} from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('demo@tradercopilot.com');
  const [password, setPassword] = useState('demo');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-white selection:bg-emerald-500/30 overflow-x-hidden font-sans">


      {/* Background Ambience */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-500/10 blur-[150px] rounded-full mix-blend-screen opacity-40"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-emerald-500/10 blur-[150px] rounded-full mix-blend-screen opacity-30"></div>
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] opacity-20"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8 lg:py-12 flex flex-col lg:flex-row items-center justify-between min-h-[calc(100vh-4rem)] gap-12 lg:gap-24">

        {/* Left: Value Proposition (Hero) */}
        <div className="flex-1 space-y-8 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-medium text-emerald-400 mb-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            System Operational v1.0
          </div>

          <h1 className="text-5xl lg:text-7xl font-bold tracking-tight leading-[1.1]">
            Institutional <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Intelligence</span> <br />
            for Retail.
          </h1>

          <p className="text-lg text-slate-400 max-w-xl leading-relaxed">
            TraderCopilot unifies <strong>Real-time Radar</strong>, <strong>AI Analysis</strong>, and <strong>Quantitative Strategies</strong> into one streamlined terminal. Stop guessing, start executing.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
            <div className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/50 bg-slate-900/30 backdrop-blur-sm">
              <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 mt-1">
                <Zap size={20} />
              </div>
              <div>
                <h3 className="font-bold text-slate-200">LITE Radar</h3>
                <p className="text-sm text-slate-500 mt-1">Real-time anomaly detection & signal feed.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/50 bg-slate-900/30 backdrop-blur-sm">
              <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400 mt-1">
                <Cpu size={20} />
              </div>
              <div>
                <h3 className="font-bold text-slate-200">PRO Analyst</h3>
                <p className="text-sm text-slate-500 mt-1">Deep-dive AI conceptualization of market structure.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/50 bg-slate-900/30 backdrop-blur-sm sm:col-span-2">
              <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400 mt-1">
                <BarChart2 size={20} />
              </div>
              <div>
                <h3 className="font-bold text-slate-200">QUANT Strategies</h3>
                <p className="text-sm text-slate-500 mt-1">Deploy autonomous trading agents with proven backtested models.</p>
              </div>
            </div>
          </div>

          <div className="pt-4 flex items-center gap-6 text-sm text-slate-500 font-medium">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-500" />
              <span>Web-First Platform</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-500" />
              <span>No Installation</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-500" />
              <span>Live Data Feed</span>
            </div>
          </div>
        </div>

        {/* Right: Login Card */}
        <div className="w-full max-w-md animate-fade-in-up delay-100">

          <div className="relative group">
            {/* Glow Effect */}
            <div className="absolute -inset-1 bg-gradient-to-br from-emerald-500/20 to-indigo-500/20 rounded-3xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-1000"></div>

            <div className="relative bg-slate-900/80 backdrop-blur-2xl rounded-2xl border border-slate-800/80 p-8 shadow-2xl">

              <div className="flex items-center justify-between mb-8">
                <div>
                  <h2 className="text-2xl font-bold text-white">Terminal Access</h2>
                  <p className="text-slate-400 text-xs mt-1">Secure Enterprise Environment</p>
                </div>
                <div className="w-12 h-12 bg-slate-800/50 rounded-xl flex items-center justify-center border border-slate-700/50">
                  <Activity className="text-emerald-400" size={24} />
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1">Identity</label>
                  <div className="relative group/input">
                    <Mail className="absolute left-3.5 top-3.5 text-slate-500 group-focus-within/input:text-emerald-400 transition-colors" size={18} />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl py-3 pl-11 pr-4 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 outline-none transition-all placeholder:text-slate-700"
                      placeholder="user@enterprise.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1">Key Phrase</label>
                  <div className="relative group/input">
                    <Lock className="absolute left-3.5 top-3.5 text-slate-500 group-focus-within/input:text-emerald-400 transition-colors" size={18} />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl py-3 pl-11 pr-4 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 outline-none transition-all placeholder:text-slate-700"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                {error && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs font-medium text-center">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-slate-950 font-bold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20 active:scale-[0.98] mt-4 group/btn"
                >
                  {loading ? <Loader2 className="animate-spin" size={20} /> : <>Initialize Session <ChevronRight size={18} className="group-hover/btn:translate-x-0.5 transition-transform" /></>}
                </button>

                <div className="text-center pt-2">
                  <Link to="/register" className="text-xs text-slate-400 hover:text-emerald-400 transition-colors">
                    Don't have an account? <span className="font-bold text-slate-300">Register Access</span>
                  </Link>
                </div>
              </form>


            </div>
          </div>
        </div>

      </div>

      {/* Footer / Status Bar */}
      <div className="fixed bottom-0 w-full border-t border-slate-800/50 bg-[#020617]/80 backdrop-blur-md py-2 px-6 flex justify-between items-center text-[10px] uppercase font-bold text-slate-600 tracking-wider z-20">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 hover:text-emerald-400 transition-colors cursor-default">
            <ShieldCheck size={12} /> Encrypted Connection
          </span>
          <span className="hidden sm:inline-block w-px h-3 bg-slate-800"></span>
          <span className="hidden sm:inline-block hover:text-indigo-400 transition-colors cursor-default">
            Latency: 24ms
          </span>
        </div>
        <div className="flex items-center gap-2">
          <TrendingUp size={12} /> Market Data Feed: <span className="text-emerald-500">Active</span>
        </div>
      </div>

    </div>
  );
};
