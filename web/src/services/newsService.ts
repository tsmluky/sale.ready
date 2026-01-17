import { api } from './api';

export interface NewsItem {
    id: number;
    title: string;
    url: string; // "url" in CryptoPanic text
    domain: string;
    published_at: string;
    currencies: { code: string; title: string; url: string }[];
    source: { title: string; region: string; domain: string };
    kind: "news" | "media";
}

export const newsService = {
    async getLatestNews(): Promise<NewsItem[]> {
        try {
            // Use the backend proxy to avoid CORS
            // Endpoint: /news/?filter=hot
            const data: any = await api.get('/news/?filter=hot&kind=news');

            if (data && data.results && Array.isArray(data.results)) {
                return data.results;
            }
            return [];
        } catch (error) {
            console.error("News Service Error (Backend Proxy):", error);
            return [];
        }
    }
};
