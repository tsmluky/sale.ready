import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Activity,
  Lock,
  Mail,
  Loader2,
  TrendingUp,
  ShieldCheck,
  Zap,
  BarChart2,
  Cpu,
  ChevronRight,
  Bot
} from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('demo@tradercopilot.com');
  const [password, setPassword] = useState('demo');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  // const { login } = useAuth(); // Mocking auth for UI preview
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      // await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate delay
      navigate('/dashboard'); // Redirect to dashboard
    } catch (err) {
      setError('Invalid credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-white selection:bg-gold-500/30 overflow-x-hidden font-sans relative">

      {/* Background Texture & Lighting (Matching Hero) */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid opacity-20" />
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-brand-900/20 rounded-full blur-[120px] mix-blend-screen opacity-40"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-gold-500/5 blur-[120px] rounded-full mix-blend-screen opacity-30"></div>
      </div>

      {/* Header/Nav for Login Page */}
      <div className="absolute top-0 left-0 w-full p-6 z-20">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="relative bg-white/5 border border-white/10 p-2 rounded-xl">
              <Bot className="h-5 w-5 text-brand-400" />
            </div>
            <span className="font-bold text-lg tracking-tight text-white hidden sm:block">TraderCopilot</span>
          </div>
          <div className="text-xs text-gray-500 font-mono">SECURE CONNECTION // TLS 1.3</div>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-20 lg:py-0 flex flex-col lg:flex-row items-center justify-between min-h-screen gap-12 lg:gap-24">

        {/* Left: Value Proposition */}
        <div className="flex-1 space-y-8 animate-in slide-in-from-bottom-5 duration-700">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass border border-gold-500/20 text-xs font-medium text-gold-400 mb-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-gold-500"></span>
            </span>
            System Operational
          </div>

          <h1 className="text-5xl lg:text-7xl font-bold tracking-tight leading-[1.1]">
            Quantitative <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-orange-500 drop-shadow-sm">Intelligence</span> <br />
            Access.
          </h1>

          <p className="text-lg text-slate-400 max-w-xl leading-relaxed font-light">
            TraderCopilot unifies <strong>Real-time Radar</strong>, <strong>AI Analysis</strong>, and <strong>Automated Strategies</strong>. <br />Enter the terminal to execute.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
            <div className="flex items-start gap-3 p-4 rounded-xl border border-white/5 bg-white/[0.02] backdrop-blur-sm">
              <div className="p-2 bg-brand-500/10 rounded-lg text-brand-400 mt-1">
                <Zap size={20} />
              </div>
              <div>
                <h3 className="font-bold text-slate-200">LITE Radar</h3>
                <p className="text-sm text-slate-500 mt-1">Real-time anomaly detection.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-xl border border-white/5 bg-white/[0.02] backdrop-blur-sm">
              <div className="p-2 bg-gold-500/10 rounded-lg text-gold-400 mt-1">
                <BarChart2 size={20} />
              </div>
              <div>
                <h3 className="font-bold text-slate-200">Backtest Lab</h3>
                <p className="text-sm text-slate-500 mt-1">Verify logic before deploying.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Login Card */}
        <div className="w-full max-w-md animate-in slide-in-from-bottom-10 duration-1000 delay-200">

          <div className="relative group">
            {/* Glow Effect */}
            <div className="absolute -inset-0.5 bg-gradient-to-br from-gold-500/20 to-brand-500/20 rounded-3xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-1000"></div>

            <div className="relative glass-card rounded-2xl p-8 shadow-2xl border border-white/10 bg-[#0f172a]/80">

              <div className="flex items-center justify-between mb-8">
                <div>
                  <h2 className="text-2xl font-bold text-white">Terminal Access</h2>
                  <p className="text-slate-400 text-xs mt-1 font-mono uppercase tracking-wide">Authorized Personnel Only</p>
                </div>
                <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center border border-white/10 shadow-inner">
                  <Activity className="text-gold-400" size={24} />
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1">Identity Key (Email)</label>
                  <div className="relative group/input">
                    <Mail className="absolute left-3.5 top-3.5 text-slate-500 group-focus-within/input:text-gold-400 transition-colors" size={18} />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-[#020617] border border-white/10 text-white rounded-xl py-3 pl-11 pr-4 focus:ring-1 focus:ring-gold-500/50 focus:border-gold-500/50 outline-none transition-all placeholder:text-slate-700 font-mono text-sm"
                      placeholder="user@quant.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1">Passphrase</label>
                  <div className="relative group/input">
                    <Lock className="absolute left-3.5 top-3.5 text-slate-500 group-focus-within/input:text-gold-400 transition-colors" size={18} />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full bg-[#020617] border border-white/10 text-white rounded-xl py-3 pl-11 pr-4 focus:ring-1 focus:ring-gold-500/50 focus:border-gold-500/50 outline-none transition-all placeholder:text-slate-700 font-mono text-sm"
                      placeholder="••••••••"
                    />
                  </div>
                  <div className="flex justify-end mt-2">
                    <Link to="/recover" className="text-xs text-slate-500 hover:text-gold-400 transition-colors font-medium">
                      Forgot password?
                    </Link>
                  </div>
                </div>

                {error && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs font-medium text-center font-mono">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-gold-500 to-orange-600 hover:from-gold-400 hover:to-orange-500 text-white font-bold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-gold-900/20 active:scale-[0.98] mt-4 group/btn"
                >
                  {loading ? <Loader2 className="animate-spin" size={20} /> : <>Initialize Session <ChevronRight size={18} className="group-hover/btn:translate-x-0.5 transition-transform" /></>}
                </button>

                <div className="text-center pt-2">
                  <Link to="/register" className="text-xs text-slate-400 hover:text-gold-400 transition-colors">
                    Don't have an account? <span className="font-bold text-white">Request Access</span>
                  </Link>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Footer / Status Bar */}
      <div className="fixed bottom-0 w-full border-t border-white/5 bg-[#020617]/80 backdrop-blur-md py-2 px-6 flex justify-between items-center text-[10px] uppercase font-bold text-slate-600 tracking-wider z-20">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 hover:text-gold-400 transition-colors cursor-default">
            <ShieldCheck size={12} /> Encrypted Connection
          </span>
          <span className="hidden sm:inline-block w-px h-3 bg-white/10"></span>
          <span className="hidden sm:inline-block hover:text-brand-400 transition-colors cursor-default">
            Latency: 24ms
          </span>
        </div>
        <div className="flex items-center gap-2">
          <TrendingUp size={12} /> Market Data: <span className="text-emerald-500">Live</span>
        </div>
      </div>
    </div>
  );
};