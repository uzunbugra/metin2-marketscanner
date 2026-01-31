"use client";

import React, { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import StatsCard from '@/components/StatsCard';
import ListingTable from '@/components/ListingTable';
import PriceChart from '@/components/PriceChart';
import { getListings, getTopItems, getPriceHistory, triggerScrape, Listing, PricePoint } from '@/lib/api';
import { TrendingUp, ShoppingCart, Server, LineChart, Search, RefreshCw } from 'lucide-react';

export default function Home() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [topItems, setTopItems] = useState<{name: string, count: number}[]>([]);
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedItemForChart, setSelectedItemForChart] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [scraping, setScraping] = useState(false);

  const fetchData = async (filter?: string | null) => {
      setLoading(true);
      setErrorMsg(null);
      try {
        const [listingsData, topItemsData] = await Promise.all([
          getListings(filter || undefined),
          getTopItems()
        ]);
        setListings(listingsData);
        setTopItems(topItemsData);

        if (topItemsData.length > 0 && !selectedItemForChart) {
            setSelectedItemForChart(topItemsData[0].name);
            const history = await getPriceHistory(topItemsData[0].name);
            setPriceHistory(history);
        }
      } catch (error: any) {
        console.error("Failed to fetch data:", error);
        setErrorMsg(error.message || "Unknown error occurred");
      } finally {
        setLoading(false);
      }
  };

  useEffect(() => {
    fetchData(null);
  }, []);

  const handleScrape = async () => {
      if (!searchQuery) return;
      setScraping(true);
      try {
          await triggerScrape(searchQuery);
          // Set filter to the searched item and refresh
          setActiveFilter(searchQuery);
          await fetchData(searchQuery);
          // Don't clear searchQuery so user sees what they searched
      } catch (e: any) {
          alert("Scrape failed: " + e.message);
      } finally {
          setScraping(false);
      }
  };

  const clearFilter = () => {
      setActiveFilter(null);
      setSearchQuery("");
      fetchData(null);
  };

  // Handle clicking a top item to view its chart
  const handleTopItemClick = async (itemName: string) => {
      setSelectedItemForChart(itemName);
      try {
          const history = await getPriceHistory(itemName);
          setPriceHistory(history);
      } catch (e) {
          console.error("Failed to fetch history for", itemName, e);
      }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      <Navbar />
      
      <main className="container mx-auto p-6 space-y-8">
        {/* Search & Scrape Control */}
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex-1 w-full">
                <h3 className="text-lg font-semibold text-white mb-2">Track New Item</h3>
                <div className="flex gap-2">
                    <input 
                        type="text" 
                        placeholder="Enter item name (e.g. Kılıç, Dolunay)" 
                        className="flex-1 bg-slate-900 border border-slate-600 rounded px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleScrape()}
                    />
                    <button 
                        onClick={handleScrape}
                        disabled={scraping || !searchQuery}
                        className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded flex items-center gap-2 font-medium transition-colors"
                    >
                        {scraping ? <RefreshCw className="animate-spin" size={20}/> : <Search size={20}/>}
                        {scraping ? "Scanning..." : "Scan Market"}
                    </button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                    Scraping takes about 10-20 seconds. Results will appear in the table below.
                </p>
            </div>
            
            <div className="flex items-center gap-4 text-slate-400 text-sm">
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    Marmara Server
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    Live Scraper
                </div>
            </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatsCard 
            title="Total Listings" 
            value={listings.length} 
            icon={ShoppingCart} 
            trend="+12% from yesterday"
          />
          <StatsCard 
            title="Active Servers" 
            value="1" 
            icon={Server} 
          />
          <StatsCard 
            title="Most Traded Item" 
            value={topItems[0]?.name || "N/A"} 
            icon={TrendingUp} 
            trend={topItems[0] ? `${topItems[0].count} listings` : ""}
          />
        </div>

        {/* Charts Section (New) */}
        {selectedItemForChart && (
            <div className="w-full">
                <div className="flex items-center gap-2 mb-4">
                    <LineChart className="text-blue-500" size={24} />
                    <h2 className="text-xl font-bold text-white">Market Analysis: {selectedItemForChart}</h2>
                </div>
                <div className="h-[400px]">
                    <PriceChart itemName={selectedItemForChart} data={priceHistory} />
                </div>
            </div>
        )}

        {/* Main Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Recent Listings Table (Wide) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <ShoppingCart className="text-blue-500" size={20} />
                  {activeFilter ? `Results for "${activeFilter}"` : "Recent Market Listings"}
                </h2>
                {activeFilter && (
                    <button 
                        onClick={clearFilter}
                        className="text-sm text-red-400 hover:text-red-300 underline"
                    >
                        Clear Filter (Show All)
                    </button>
                )}
            </div>
            {errorMsg && (
                <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded mb-4">
                    Error loading data: {errorMsg}
                </div>
            )}
            {loading ? (
               <div className="text-center py-10 text-slate-500">Loading market data...</div>
            ) : (
               <ListingTable listings={listings} />
            )}
          </div>

          {/* Sidebar / Top Items */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <TrendingUp className="text-green-500" size={20} />
              Top Trending Items
            </h2>
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
              {topItems.length === 0 ? (
                <div className="text-slate-500 text-sm">No trending data yet.</div>
              ) : (
                <ul className="space-y-3">
                  {topItems.map((item, idx) => (
                    <li 
                        key={idx} 
                        className="flex justify-between items-center border-b border-slate-700 pb-2 last:border-0 last:pb-0 cursor-pointer hover:bg-slate-700/50 p-2 rounded transition-colors"
                        onClick={() => handleTopItemClick(item.name)}
                    >
                      <span className="text-slate-300 font-medium">{idx + 1}. {item.name}</span>
                      <span className="text-blue-400 font-bold">{item.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="text-xs text-slate-500 text-center">
                Click an item to view price history
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
