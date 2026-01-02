import React from 'react';
import { MemoryRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { DashboardHome } from './components/dashboard/DashboardHome';
import { HistoryPage } from './pages/HistoryPage';
import LandingPage from './pages/LandingPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { ScannerPage } from './pages/ScannerPage';
import { StrategiesPage } from './pages/StrategiesPage';
import { StrategyDetailsPage } from './pages/StrategyDetailsPage';
import { BacktestPage } from './pages/BacktestPage';

import { AdvisorPage } from './pages/AdvisorPage';
import { PricingPage } from './pages/PricingPage';
import { AdminPage } from './pages/AdminPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastContainer } from './components/Toast';
import { CopilotProvider } from './context/CopilotContext';
import { Loader2 } from 'lucide-react';
import { AdvisorChat } from './components/AdvisorChat';
import { CopilotModal } from './components/copilot/CopilotModal';
import { CopilotFAB } from './components/copilot/CopilotFAB';

// Wrapper for Protected Routes
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="h-screen flex items-center justify-center bg-[#020617] text-indigo-500">
                <Loader2 className="animate-spin" size={32} />
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <MainLayout>{children}</MainLayout>;
};

const App: React.FC = () => {
    return (
        <AuthProvider>
            <ThemeProvider>
                <CopilotProvider>
                    <Router>
                        <ToastContainer />
                        <Routes>
                            <Route path="/login" element={<LoginPage />} />
                            <Route path="/register" element={<RegisterPage />} />

                            {/* Protected Routes */}
                            <Route path="/" element={<LandingPage />} />

                            {/* Protected Routes */}
                            <Route
                                path="/dashboard"
                                element={
                                    <ProtectedRoute>
                                        <DashboardHome />
                                    </ProtectedRoute>
                                }
                            />
                            <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
                            <Route path="/scanner" element={<ProtectedRoute><ScannerPage /></ProtectedRoute>} />
                            <Route path="/strategies" element={<ProtectedRoute><StrategiesPage /></ProtectedRoute>} />
                            <Route path="/strategies/:id" element={<ProtectedRoute><StrategyDetailsPage /></ProtectedRoute>} />
                            {/* Mapping old signals path effectively to scanner in case of bookmarks, or just replacing it entirely */}
                            <Route path="/signals" element={<Navigate to="/scanner" replace />} />
                            <Route path="/analysis" element={<ProtectedRoute><AnalysisPage /></ProtectedRoute>} />
                            <Route path="/advisor" element={<ProtectedRoute><AdvisorPage /></ProtectedRoute>} />

                            <Route path="/backtest" element={<ProtectedRoute><BacktestPage /></ProtectedRoute>} />
                            <Route path="/pricing" element={<ProtectedRoute><PricingPage /></ProtectedRoute>} />
                            <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
                            <Route path="/profile" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
                            <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} /> {/* Added AdminPage route */}

                            {/* Fallback */}
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                        <CopilotModal />
                        <CopilotFAB />



                    </Router>
                </CopilotProvider>
            </ThemeProvider>
        </AuthProvider>
    );
};

export default App;
