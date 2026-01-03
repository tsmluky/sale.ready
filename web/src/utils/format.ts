export const formatPrice = (price: number | string | undefined | null): string => {
    if (price === undefined || price === null) return '-';

    const p = Number(price);
    if (isNaN(p)) return '-';
    if (p === 0) return '0.00';

    // Crypto Formatting Rules (Dynamic Precision)
    if (p < 0.0001) return p.toFixed(8);      // PEPE/SHIB: 0.00000650
    if (p < 0.01) return p.toFixed(6);        // Low cap: 0.001234
    if (p < 1) return p.toFixed(4);           // DOGE/ADA: 0.1419
    if (p < 50) return p.toFixed(3);          // Mid-range: 25.123
    return p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); // BTC/ETH: 96,123.50
};

export const formatRelativeTime = (dateStr: string | undefined): string => {
    if (!dateStr) return '-';
    // Ensure UTC if missing Z
    const safeDate = dateStr.endsWith('Z') ? dateStr : `${dateStr}Z`;
    const date = new Date(safeDate);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    // Future handling
    if (diff < 0) return 'Just now';

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
};
