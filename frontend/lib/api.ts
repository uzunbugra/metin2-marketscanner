import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(request => {
  console.log('Starting Request', JSON.stringify(request, null, 2))
  return request
})

api.interceptors.response.use(response => {
  return response
}, error => {
    console.error("API Error:", error);
    return Promise.reject(error);
});

export interface Listing {
  id: number;
  item: {
    name: string;
    category: string;
    image_url: string | null;
  };
  server: {
    name: string;
  };
  seller_name: string;
  quantity: number;
  price_won: number;
  price_yang: number;
  total_price_yang: number;
  seen_at: string;
  bonuses: {
    bonus_name: string;
    bonus_value: string;
  }[];
}

export const getListings = async (itemName?: string) => {
  const params: any = {};
  if (itemName) params.item_name = itemName;
  
  const response = await api.get<Listing[]>('/market/listings', { params });
  return response.data;
};

export const getTopItems = async () => {
    const response = await api.get<{name: string, count: number}[]>('/market/stats/top-items');
    return response.data;
}

export interface PricePoint {
  date: string;
  avg_price: number;
}

export const getPriceHistory = async (itemName: string) => {
    const response = await api.get<PricePoint[]>('/market/stats/price-history', {
        params: { item_name: itemName }
    });
    return response.data;
}

export const triggerScrape = async (query: string) => {
    const response = await api.post<{ message: string, output?: string, error?: string }>('/scrape', { query });
    return response.data;
}
