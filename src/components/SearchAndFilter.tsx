import React from "react";
import { Search, Plus, Activity, Star } from "lucide-react";

export const FILTER_CATEGORIES = [
  "All",
  "★ Favorites",
  "Gaming",
  "Bypass / Anti-Sanction",
  "AdBlock & Security",
  "Global",
  "Custom",
] as const;

export type FilterCategory = typeof FILTER_CATEGORIES[number];

interface SearchAndFilterProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  onPingAll: () => void;
  isPingingAll: boolean;
  onOpenCustomModal: () => void;
}

export const SearchAndFilter: React.FC<SearchAndFilterProps> = ({
  searchQuery,
  onSearchChange,
  selectedCategory,
  onSelectCategory,
  onPingAll,
  isPingingAll,
  onOpenCustomModal,
}) => {
  return (
    <div className="flex flex-col gap-2 shrink-0">
      {/* Top Row: Search Input + Ping All + Add Custom DNS */}
      <div className="flex items-center justify-between gap-2.5 w-full">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search DNS by name, IP, or tag..."
            className="w-full pl-8 pr-7 py-1.5 bg-slate-900/90 border border-slate-700/80 focus:border-indigo-500 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all shadow-inner h-8"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 text-xs px-1"
            >
              ×
            </button>
          )}
        </div>

        {/* Action Buttons: Ping All & Custom DNS */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={onPingAll}
            disabled={isPingingAll}
            title="Concurrently test UDP DNS resolution latency for all servers"
            className="h-8 flex items-center gap-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition-all active:scale-95 disabled:opacity-50 shadow-sm"
          >
            <Activity
              className={`w-3.5 h-3.5 text-emerald-400 ${
                isPingingAll ? "animate-spin" : ""
              }`}
            />
            <span>{isPingingAll ? "Pinging..." : "Ping All"}</span>
          </button>

          <button
            type="button"
            onClick={onOpenCustomModal}
            className="h-8 flex items-center gap-1.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold transition-all active:scale-95 shadow-md shadow-emerald-950/40"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Custom DNS</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: 7 Consolidated Filter Pills (Zero Horizontal Scrollbar) */}
      <div className="flex items-center gap-1.5 w-full overflow-hidden">
        {FILTER_CATEGORIES.map((cat) => {
          const isSelected = selectedCategory === cat;
          const isFav = cat === "★ Favorites";

          return (
            <button
              key={cat}
              type="button"
              onClick={() => onSelectCategory(cat)}
              className={`h-7 px-2.5 rounded-lg text-[11px] font-medium border transition-all whitespace-nowrap flex items-center gap-1 shrink-0 ${
                isSelected
                  ? isFav
                    ? "bg-amber-500/25 text-amber-300 border-amber-500/60 shadow-sm font-semibold"
                    : "bg-indigo-600 text-white border-indigo-500 shadow-sm font-semibold"
                  : "bg-slate-900/70 text-slate-400 border-slate-800/80 hover:text-slate-200 hover:bg-slate-800/80 hover:border-slate-700"
              }`}
            >
              {isFav && <Star className="w-3 h-3 fill-amber-400 text-amber-400" />}
              <span>{isFav ? "Favorites" : cat}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
