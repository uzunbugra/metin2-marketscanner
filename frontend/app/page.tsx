"use client";

import React, { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import StatsCard from '@/components/StatsCard';
import ListingTable from '@/components/ListingTable';
import PriceChart from '@/components/PriceChart';
import { getListings, getTopItems, getPriceHistory, triggerScrape, getServers, Listing, PricePoint } from '@/lib/api';
import { TrendingUp, ShoppingCart, Server, LineChart, Search, RefreshCw, ChevronDown } from 'lucide-react';

export default function Home() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [topItems, setTopItems] = useState<{name: string, count: number}[]>([]);
  const [servers, setServers] = useState<{id: number, name: string}[]>([]);
  const [selectedServer, setSelectedServer] = useState<string>("Marmara");
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedItemForChart, setSelectedItemForChart] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [scraping, setScraping] = useState(false);
  const [upgradeFilter, setUpgradeFilter] = useState<string>("ALL");

  // Helper to extract plus value from item name
  const getPlusValue = (name: string): number | null => {
    // Looks for + followed by digits, ideally at the end or before a bracket
    const match = name.match(/\+(\d+)/);
    return match ? parseInt(match[1]) : null;
  };

  const fetchData = async (filter?: string | null, serverName?: string) => {
      setLoading(true);
      setErrorMsg(null);
      const currentServer = serverName || selectedServer;
      try {
        const [listingsData, topItemsData, serversData] = await Promise.all([
          getListings(filter || undefined, currentServer),
          getTopItems(),
          getServers()
        ]);
        setListings(listingsData);
        setTopItems(topItemsData);
        setServers(serversData);

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
    fetchData(null, selectedServer);
  }, [selectedServer]);

  const handleScrape = async () => {
      if (!searchQuery) return;
      setScraping(true);
      try {
          await triggerScrape(searchQuery, selectedServer);
          // Set filter to the searched item and refresh
          setActiveFilter(searchQuery);
          await fetchData(searchQuery, selectedServer);
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
      setUpgradeFilter("ALL");
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

  // Filter listings based on upgrade level
  const filteredListings = listings.filter(item => {
      const plus = getPlusValue(item.item.name);
      
      if (upgradeFilter === "ALL") return true;
      if (upgradeFilter === "MATERIAL") return plus === null;
      if (upgradeFilter === "0-6") return plus !== null && plus >= 0 && plus <= 6;
      if (upgradeFilter === "7-8") return plus !== null && plus >= 7 && plus <= 8;
      if (upgradeFilter === "9") return plus === 9;
      if (upgradeFilter === "10+") return plus !== null && plus >= 10;
      return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      <Navbar />
      
      <main className="container mx-auto p-6 space-y-8">
        {/* Search & Scrape Control */}
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 flex flex-col gap-4">
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
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
                </div>
                
                <div className="flex items-center gap-4 text-slate-400 text-sm self-end mb-2">
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

            {/* Upgrade Level Filter */}
            <div className="border-t border-slate-700 pt-4">
                <span className="text-sm text-slate-400 mr-4">Filter by Level:</span>
                <div className="inline-flex flex-wrap gap-2">
                    {[
                        { id: "ALL", label: "All Items" },
                        { id: "MATERIAL", label: "Materials (No +)" },
                        { id: "0-6", label: "+0 to +6" },
                        { id: "7-8", label: "+7 to +8" },
                        { id: "9", label: "+9 Only" },
                        { id: "10+", label: "+10 & Higher" }
                    ].map(filter => (
                        <button
                            key={filter.id}
                            onClick={() => setUpgradeFilter(filter.id)}
                            className={`px-3 py-1 rounded text-sm transition-colors ${
                                upgradeFilter === filter.id 
                                ? "bg-blue-600 text-white font-medium" 
                                : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                            }`}
                        >
                            {filter.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatsCard 
            title="Total Listings" 
            value={filteredListings.length} 
            icon={ShoppingCart} 
            trend={upgradeFilter !== "ALL" ? "Filtered View" : "+12% from yesterday"}
          />
          
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 relative group">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-slate-400 font-medium">Selected Server</h3>
                <Server className="text-blue-500" size={20} />
            </div>
            <div className="relative">
                <select 
                    value={selectedServer}
                    onChange={(e) => setSelectedServer(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-white font-bold appearance-none focus:outline-none focus:border-blue-500 cursor-pointer"
                >
                    {servers.map(server => (
                        <option key={server.id} value={server.name}>
                            {server.name}
                        </option>
                    ))}
                    {servers.length === 0 && <option value="Marmara">Marmara</option>}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" size={16} />
            </div>
            <div className="text-xs text-blue-500 mt-2 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                Switching filters results automatically
            </div>
          </div>

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
               <ListingTable listings={filteredListings} />
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
