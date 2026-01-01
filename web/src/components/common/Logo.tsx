import React from 'react';
import { Zap } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

interface LogoProps {
    className?: string;
    variant?: 'full' | 'icon';
    size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Logo: React.FC<LogoProps> = ({ className = '', variant = 'full', size = 'md' }) => {
    const { theme } = useTheme();

    const sizeClasses = {
        sm: { container: 'w-8 h-8 rounded-lg', icon: 'w-4 h-4', text: 'text-base' },
        md: { container: 'w-10 h-10 rounded-xl', icon: 'w-5 h-5', text: 'text-lg' },
        lg: { container: 'w-12 h-12 rounded-2xl', icon: 'w-6 h-6', text: 'text-xl' },
        xl: { container: 'w-16 h-16 rounded-2xl', icon: 'w-8 h-8', text: 'text-2xl' },
    };

    const currentSize = sizeClasses[size];

    return (
        <div className={`flex items-center gap-3 group cursor-pointer select-none ${className}`}>
            <div className={`${currentSize.container} bg-gradient-to-br from-gold-500 to-orange-600 flex items-center justify-center text-white shadow-lg shadow-gold-500/20 group-hover:shadow-gold-500/40 transition-all duration-300 relative overflow-hidden`}>
                {/* Inner Shine Effect */}
                <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                {theme.logoUrl && theme.logoUrl.startsWith('http') ? (
                    <img src={theme.logoUrl} alt="Logo" className={currentSize.icon} />
                ) : (
                    <Zap className={`${currentSize.icon} fill-white drop-shadow-sm`} />
                )}
            </div>

            {variant === 'full' && (
                <div className="flex flex-col">
                    <span className={`font-black tracking-tight text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gold-200 transition-all duration-300 ${currentSize.text}`}>
                        {theme.appName}
                    </span>
                    <span className="text-[10px] text-gold-400 font-bold tracking-widest uppercase opacity-80 group-hover:opacity-100 transition-opacity">
                        Copilot Console
                    </span>
                </div>
            )}
        </div>
    );
};
