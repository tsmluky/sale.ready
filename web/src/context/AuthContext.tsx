import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile } from '../types';
import { api } from '../services/api';

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    userProfile: UserProfile | null;
    login: (email?: string, password?: string) => Promise<void>;
    logout: () => void;
    completeOnboarding: () => void;
    updateProfile: (name: string, favorites: string[]) => Promise<void>;
    updateSignalNote: (timestamp: string, token: string, note: string) => Promise<void>;
    toggleFollow: (signal: any) => void;
    upgradeSubscription: (planId: 'free' | 'trader' | 'pro') => Promise<void>;
    refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('auth_token');
            if (token) {
                try {
                    // Validate token with backend
                    const data = await api.getMe();

                    // Fetch Entitlements (Permissions/Tokens)
                    let allowedTokens = ['BTC', 'ETH', 'SOL'];
                    try {
                        const ent = await api.get('/auth/me/entitlements');
                        if (ent && ent.allowed_tokens) {
                            allowedTokens = ent.allowed_tokens;
                        }
                    } catch (e) {
                        console.warn('Failed to fetch entitlements', e);
                    }

                    // Map Backend Plan (FREE, PRO, OWNER) to Frontend (free, trader, pro)
                    const backendPlan = data.plan?.toUpperCase() || 'FREE';
                    let frontendPlan: 'free' | 'trader' | 'pro' = 'free';

                    if (backendPlan === 'TRADER') frontendPlan = 'trader';
                    if (backendPlan === 'PRO') frontendPlan = 'pro';
                    if (backendPlan === 'OWNER') frontendPlan = 'pro'; // Owner gets top tier

                    setUserProfile({
                        user: {
                            ...data,
                            role: data.role, // ensure role is passed
                            subscription_status: frontendPlan,
                            onboarding_completed: localStorage.getItem('onboarding_completed') === 'true',
                            avatar_url: data.avatar_url || `https://ui-avatars.com/api/?name=${data.name}&background=10b981&color=fff`,
                            allowed_tokens: allowedTokens
                        },
                        preferences: {
                            favorite_tokens: ['eth', 'btc'],
                            default_timeframe: '30m',
                            notifications: { trade_updates: true, market_volatility: true, system_status: true }
                        },
                        portfolio: { followed_signals: JSON.parse(localStorage.getItem('followed_signals') || '[]') }
                    });
                    setIsAuthenticated(true);
                } catch (err) {
                    console.error('Token validation failed', err);
                    const msg = String(err);
                    // Aggressive Logout on 401/403 OR generic fetch failure on startup
                    // If we can't get the user profile, the token is effectively useless.
                    if (
                        msg.includes('401') ||
                        msg.includes('403') ||
                        msg.includes('Unauthorized') ||
                        msg.includes('Failed to fetch user profile') // Catch the generic error from api.ts
                    ) {
                        console.warn('Invalid token detected. Logging out.');
                        localStorage.removeItem('auth_token');
                        setIsAuthenticated(false);
                    } else {
                        // Only keep session if it looks like a transient network issue
                        console.warn("Network error during auth check. Keeping session active.");
                        setIsAuthenticated(true);
                    }
                }
            }
            setIsLoading(false);
        };
        checkAuth();
    }, []);

    const login = async (email?: string, password?: string) => {
        setIsLoading(true);
        try {
            // For demo simplicity, we still support the mock bypass if no creds are passed, 
            // but if creds ARE passed, we use real API.
            if (email && password) {
                const data = await api.login(email, password);
                localStorage.setItem('auth_token', data.access_token);

                // Fetch profile immediately
                const user = data.user;
                // Map Backend Plan (FREE, PRO, OWNER) to Frontend (free, trader, pro)
                const backendPlan = user.plan?.toUpperCase() || 'FREE';
                let frontendPlan: 'free' | 'trader' | 'pro' = 'free';

                if (backendPlan === 'TRADER') frontendPlan = 'trader';
                if (backendPlan === 'PRO') frontendPlan = 'pro';
                if (backendPlan === 'OWNER') frontendPlan = 'pro';

                setUserProfile({
                    user: {
                        ...user,
                        role: user.role,
                        subscription_status: frontendPlan,
                        onboarding_completed: false,
                        avatar_url: `https://ui-avatars.com/api/?name=${user.name}&background=10b981&color=fff`
                    },
                    preferences: {
                        favorite_tokens: ['eth', 'btc'],
                        default_timeframe: '30m',
                        notifications: { trade_updates: true, market_volatility: true, system_status: true }
                    },
                    portfolio: { followed_signals: [] }
                });
                setIsAuthenticated(true);
            } else {
                throw new Error("Credentials required");
            }
        } catch (err) {
            console.error('Login failed', err);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        setIsAuthenticated(false);
        setUserProfile(null);
        localStorage.removeItem('auth_token');
    };

    const completeOnboarding = () => {
        if (userProfile) {
            const updatedProfile = {
                ...userProfile,
                user: {
                    ...userProfile.user,
                    onboarding_completed: true
                }
            };
            setUserProfile(updatedProfile);
            localStorage.setItem('onboarding_completed', 'true');
        }
    };

    const updateProfile = async (name: string, favorites: string[]) => {
        if (!userProfile) return;
        await new Promise(resolve => setTimeout(resolve, 500));
        setUserProfile({
            ...userProfile,
            user: { ...userProfile.user, name },
            preferences: { ...userProfile.preferences, favorite_tokens: favorites }
        });
    };

    const updateSignalNote = async (timestamp: string, token: string, note: string) => {
        console.log('Updating signal note:', { timestamp, token, note });
        await new Promise(resolve => setTimeout(resolve, 500));
    };

    const toggleFollow = (signal: any) => {
        if (!userProfile) return;

        const currentFollowed = userProfile.portfolio?.followed_signals || [];
        const isFollowed = currentFollowed.some(
            (s) => s.timestamp === signal.timestamp && s.token === signal.token
        );

        let updatedFollowed;
        if (isFollowed) {
            updatedFollowed = currentFollowed.filter(
                (s) => !(s.timestamp === signal.timestamp && s.token === signal.token)
            );
        } else {
            updatedFollowed = [
                ...currentFollowed,
                {
                    timestamp: signal.timestamp,
                    token: signal.token,
                    direction: signal.direction,
                    entry: signal.entry,
                    tp: signal.tp,
                    sl: signal.sl,
                    note: '',
                },
            ];
        }

        const updatedProfile = {
            ...userProfile,
            portfolio: {
                ...userProfile.portfolio,
                followed_signals: updatedFollowed,
            },
        };

        setUserProfile(updatedProfile);
        localStorage.setItem('followed_signals', JSON.stringify(updatedFollowed));
    };

    const upgradeSubscription = async (planId: 'free' | 'trader' | 'pro') => {
        setIsLoading(true);
        // Real implementation - Call Admin API to update plan
        try {
            if (!userProfile?.user?.id) throw new Error('No user ID');

            // Map frontend plan to backend plan
            let backendPlan = planId.toUpperCase();

            await api.updateUserPlan(userProfile.user.id, backendPlan);

            // Refresh profile to update UI
            await refreshProfile();

            console.log(`Plan upgraded to ${planId}`);
            // Persist to local storage to survive refresh if needed
            localStorage.setItem('user_plan', planId);
        } catch (error) {
            console.error('Failed to upgrade subscription', error);
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    const refreshProfile = async () => {
        // Re-runs the checkAuth logic essentially (fetching /me)
        const token = localStorage.getItem('auth_token');
        if (!token) return;

        try {
            const data = await api.getMe();
            // Fetch Entitlements (Permissions/Tokens)
            let allowedTokens = ['BTC', 'ETH', 'SOL'];
            try {
                const ent = await api.get('/auth/me/entitlements');
                if (ent && ent.allowed_tokens) {
                    allowedTokens = ent.allowed_tokens;
                }
            } catch (e) {
                console.warn('Failed to fetch entitlements', e);
            }

            const backendPlan = data.plan?.toUpperCase() || 'FREE';
            let frontendPlan: 'free' | 'trader' | 'pro' = 'free';
            if (backendPlan === 'TRADER') frontendPlan = 'trader';
            if (backendPlan === 'PRO') frontendPlan = 'pro';
            if (backendPlan === 'OWNER') frontendPlan = 'pro';

            setUserProfile({
                user: {
                    ...data,
                    role: data.role,
                    subscription_status: frontendPlan,
                    onboarding_completed: localStorage.getItem('onboarding_completed') === 'true',
                    avatar_url: data.avatar_url || `https://ui-avatars.com/api/?name=${data.name}&background=10b981&color=fff`,
                    allowed_tokens: allowedTokens
                },
                preferences: userProfile?.preferences || {
                    favorite_tokens: ['eth', 'btc'],
                    default_timeframe: '30m',
                    notifications: { trade_updates: true, market_volatility: true, system_status: true }
                },
                portfolio: userProfile?.portfolio || { followed_signals: JSON.parse(localStorage.getItem('followed_signals') || '[]') }
            });
        } catch (err) {
            console.error('Refresh profile failed', err);
        }
    };

    return (
        <AuthContext.Provider
            value={{
                isAuthenticated,
                isLoading,
                userProfile,
                login,
                logout,
                completeOnboarding,
                updateProfile,
                updateSignalNote,
                toggleFollow,
                upgradeSubscription,
                refreshProfile,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
