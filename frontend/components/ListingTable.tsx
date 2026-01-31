import React from 'react';
import { Listing } from '@/lib/api';

interface ListingTableProps {
  listings: Listing[];
}

// Max bonus values map
const MAX_BONUSES: Record<string, number> = {
  // Stats
  "Zeka": 12,
  "Güç": 12,
  "Çeviklik": 12,
  "Canlılık": 12,
  "Yaşam Enerjisi": 12,
  
  // Defenses
  "Kılıç Savunması": 15,
  "Çift El Savunması": 15,
  "Bıçak Savunması": 15,
  "Çan Savunması": 15,
  "Yelpaze Savunması": 15,
  "Ok Savunması": 15,
  "Büyüye Karşı Dayanıklılık": 15,
  "Şimşeğe Karşı Dayanıklılık": 15,
  "Rüzgara Karşı Dayanıklılık": 15,
  "Ateşe Karşı Dayanıklılık": 15,
  
  // Strong Against
  "Yarı İnsanlara Karşı Güçlü": 10, // Common max. Can be higher on specific items.
  "Ölümsüzlere karşı güçlü": 20,
  "Şeytanlara karşı güçlü": 20,
  "Hayvanlara karşı güçlü": 20,
  "Mistiklere karşı güçlü": 20,
  "Orklara karşı güçlü": 20,
  
  // Combat
  "Kritik Vuruş Şansı": 10,
  "Delici Vuruş Şansı": 10,
  "Zehirleme şansı": 8,
  "Sersemletme şansı": 8,
  "Yavaşlatma şansı": 8,
  "Büyü Hızı": 20,
  "Saldırı Değeri": 50,
  "Saldırı Hızı": 8,
  
  // Special
  "Max HP": 2000,
  "EXP Bonus Şansı": 20,
  "İki kat eşya düşürme şansı": 20,
  "HP Üretimi": 30,
  "SP Üretimi": 30,
  "Hasar HP Tarafından Emilecek": 10,
  "Hasar SP Tarafından Emilecek": 10,
  "Vücut darbelerini yansıtma şansı": 15,
  "Beden karşısındaki atakların bloklanması": 15,
  "Ortalama Zarar": 50, // Highlight high avg damage (usually 50+ is great)
  "Beceri Hasarı": 20, // Highlight high skill damage
};

// Helper to extract numeric value from bonus string and check against max
const isMaxBonus = (bonusStr: string): boolean => {
  // Normalize string using Turkish locale for accurate matching (e.g. I -> ı, İ -> i)
  const normalizedBonus = bonusStr.toLocaleLowerCase('tr');
  
  for (const [key, maxVal] of Object.entries(MAX_BONUSES)) {
    const normalizedKey = key.toLocaleLowerCase('tr');
    
    if (normalizedBonus.includes(normalizedKey)) {
      // Extract number: look for digits
      const matches = bonusStr.match(/(\d+)/g);
      if (matches) {
        for (const m of matches) {
           if (parseInt(m) >= maxVal) return true;
        }
      }
    }
  }
  return false;
};

export default function ListingTable({ listings }: ListingTableProps) {
  return (
    <div className="overflow-x-auto bg-slate-800 rounded-lg border border-slate-700">
      <table className="w-full text-left text-sm text-slate-400">
        <thead className="bg-slate-900 text-slate-200 uppercase font-medium">
          <tr>
            <th className="px-6 py-4">Item Name & Bonuses</th>
            <th className="px-6 py-4">Qty</th>
            <th className="px-6 py-4">Price (Won)</th>
            <th className="px-6 py-4">Price (Yang)</th>
            <th className="px-6 py-4">Seller</th>
            <th className="px-6 py-4">Seen At</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700">
          {listings.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                No listings found.
              </td>
            </tr>
          ) : (
            listings.map((listing) => (
              <tr key={listing.id} className="hover:bg-slate-700/50 transition-colors">
                <td className="px-6 py-4 align-top">
                    <div className="font-bold text-white text-base mb-2">
                        {listing.item.name}
                    </div>
                    {listing.bonuses && listing.bonuses.length > 0 && (
                        <ul className="space-y-1">
                            {listing.bonuses.map((bonus, idx) => {
                                const isMax = isMaxBonus(bonus.bonus_name);
                                return (
                                    <li 
                                        key={idx} 
                                        className={`text-xs px-2 py-0.5 rounded w-fit ${
                                            isMax 
                                            ? "text-purple-400 font-bold bg-purple-900/30 border border-purple-500/30" 
                                            : "text-slate-400 bg-slate-800/50"
                                        }`}
                                    >
                                        {bonus.bonus_name}
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </td>
                <td className="px-6 py-4 align-top">{listing.quantity}</td>
                <td className="px-6 py-4 text-yellow-500 font-bold align-top text-lg">{listing.price_won} W</td>
                <td className="px-6 py-4 align-top">{listing.price_yang.toLocaleString()}</td>
                <td className="px-6 py-4 text-blue-400 align-top">{listing.seller_name}</td>
                <td className="px-6 py-4 text-slate-500 align-top text-xs">
                  {new Date(listing.seen_at).toLocaleString()}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}