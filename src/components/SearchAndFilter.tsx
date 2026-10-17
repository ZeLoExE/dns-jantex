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
            className="w-full pl-8 pr-7 py-1.5 bg-white border border-slate-300 focus:border-indigo-500 rounded-xl text-xs font-medium text-slate-900 placeholder-slate-400 shadow-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all dark:bg-slate-900/90 dark:border-slate-700/80 dark:text-slate-100 dark:placeholder-slate-500 dark:shadow-inner h-8"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs px-1"
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
            className="h-8 flex items-center gap-1.5 px-3 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 rounded-xl text-xs font-semibold transition-all active:scale-95 disabled:opacity-50 shadow-sm dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 dark:border-slate-700/80 dark:shadow-none"
          >
            <Activity
              className={`w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 ${
                isPingingAll ? "animate-spin" : ""
              }`}
            />
            <span>{isPingingAll ? "Pinging..." : "Ping All"}</span>
          </button>

          <button
            type="button"
            onClick={onOpenCustomModal}
            className="h-8 flex items-center gap-1.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold transition-all active:scale-95 shadow-md shadow-emerald-950/20"
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
              className={`h-7 px-2.5 rounded-lg text-[11px] border transition-all whitespace-nowrap flex items-center gap-1 shrink-0 ${
                isSelected
                  ? isFav
                    ? "bg-amber-100 text-amber-900 border-amber-400 shadow-xs font-semibold dark:bg-amber-500/25 dark:text-amber-300 dark:border-amber-500/60"
                    : "bg-indigo-600 text-white border-indigo-600 shadow-sm font-semibold dark:border-indigo-500"
                  : "bg-white text-slate-700 border-slate-300 shadow-xs hover:bg-slate-50 hover:text-slate-900 hover:border-slate-400 font-medium dark:bg-slate-900/70 dark:text-slate-400 dark:border-slate-800/80 dark:shadow-none dark:hover:text-slate-200 dark:hover:bg-slate-800/80 dark:hover:border-slate-700"
              }`}
            >
              {isFav && <Star className="w-3 h-3 fill-amber-500 text-amber-500 dark:fill-amber-400 dark:text-amber-400" />}
              <span>{isFav ? "Favorites" : cat}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
