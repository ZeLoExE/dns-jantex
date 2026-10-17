import React, { useState } from "react";
import {
  Star,
  Copy,
  Check,
  Activity,
  Trash2,
  ArrowRight,
  WifiOff,
} from "lucide-react";
import { DnsServer } from "../types";

interface DnsCardProps {
  dns: DnsServer;
  isActive: boolean;
  onApply: (dns: DnsServer) => void;
  onToggleFavorite: (id: string) => void;
  onPing: (id: string) => void;
  onDelete?: (id: string) => void;
  isPinging: boolean;
  isApplying: boolean;
}

export const DnsCard: React.FC<DnsCardProps> = ({
  dns,
  isActive,
  onApply,
  onToggleFavorite,
  onPing,
  onDelete,
  isPinging,
  isApplying,
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 1200);
  };

  const renderLatencyBadge = () => {
    if (isPinging) {
      return (
        <span className="flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-300 text-indigo-800 dark:bg-slate-800 dark:border-indigo-500/40 dark:text-indigo-300 shadow-xs">
          <Activity className="w-2.5 h-2.5 animate-spin text-indigo-600 dark:text-indigo-400" />
          <span>Testing...</span>
        </span>
      );
    }

    if (dns.latency_ms === null || dns.latency_ms === undefined) {
      return (
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 border border-slate-300 text-slate-600 dark:bg-slate-800/80 dark:border-slate-700/60 dark:text-slate-500">
          -- ms
        </span>
      );
    }

    if (dns.latency_ms === -1) {
      return (
        <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 border border-rose-300 text-rose-800 dark:bg-rose-500/15 dark:border-rose-500/40 dark:text-rose-400 shadow-xs">
          <WifiOff className="w-2.5 h-2.5 text-rose-600 dark:text-rose-400" />
          <span>Timeout</span>
        </span>
      );
    }

    const ms = dns.latency_ms;
    let badgeClass = "bg-emerald-50 border-emerald-300 text-emerald-800 dark:bg-emerald-500/15 dark:border-emerald-500/30 dark:text-emerald-300";
    if (ms > 100) {
      badgeClass = "bg-orange-50 border-orange-300 text-orange-800 dark:bg-orange-500/15 dark:border-orange-500/30 dark:text-orange-400";
    } else if (ms >= 50) {
      badgeClass = "bg-amber-50 border-amber-300 text-amber-800 dark:bg-amber-500/15 dark:border-amber-500/30 dark:text-amber-300";
    }

    return (
      <span
        className={`flex items-center gap-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border shadow-xs ${badgeClass}`}
      >
        <span className="w-1 h-1 rounded-full bg-current" />
        {ms} ms
      </span>
    );
  };

  return (
    <div
      className={`rounded-xl p-3 bg-white border transition-all flex flex-col justify-between gap-2.5 select-none ${
        isActive
          ? "border-emerald-500 ring-1 ring-emerald-500/30 shadow-md shadow-emerald-500/10 bg-emerald-50/70 dark:bg-emerald-950/15 dark:border-emerald-500/50 dark:shadow-none"
          : "border-slate-200/90 shadow-md shadow-slate-900/[0.06] hover:shadow-lg hover:border-slate-300 dark:bg-slate-900/70 dark:border-slate-800/80 dark:shadow-none dark:hover:border-slate-700"
      }`}
    >
      {/* Row 1 (Header): Favorite + Name + ACTIVE badge + Tags + Delete */}
      <div className="flex items-center justify-between gap-2">
        {/* Left: Star + Server Name + ACTIVE badge */}
        <div className="flex items-center gap-1.5 min-w-0 flex-1">
          <button
            type="button"
            onClick={() => onToggleFavorite(dns.id)}
            title={dns.is_favorite ? "Remove from Favorites" : "Add to Favorites"}
            className="p-0.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-all shrink-0"
          >
            <Star
              className={`w-3.5 h-3.5 transition-all ${
                dns.is_favorite
                  ? "fill-amber-400 text-amber-400 scale-105"
                  : "text-slate-400 dark:text-slate-600 hover:text-slate-600 dark:hover:text-slate-400"
              }`}
            />
          </button>

          <span
            className="font-bold text-xs text-slate-900 tracking-tight drop-shadow-[0_1px_1px_rgba(0,0,0,0.04)] dark:text-slate-100 dark:drop-shadow-none truncate"
            title={dns.name}
          >
            {dns.name}
          </span>

          {isActive && (
            <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-900 border border-emerald-400/80 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30 shrink-0 shadow-xs">
              ACTIVE
            </span>
          )}
        </div>

        {/* Right: Max 2 Compact Tags + Delete Icon */}
        <div className="flex items-center gap-1 shrink-0">
          {dns.tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-300 font-medium dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700/40 truncate max-w-[70px]"
              title={tag}
            >
              {tag}
            </span>
          ))}

          {onDelete && (
            <button
              type="button"
              onClick={() => onDelete(dns.id)}
              title="Delete Custom DNS"
              className="p-1 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:text-slate-500 dark:hover:text-rose-400 dark:hover:bg-rose-500/10 rounded transition-colors"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Row 2 (IP Addresses — Compact Inline Box) */}
      <div className="grid grid-cols-2 gap-2 bg-slate-100/90 dark:bg-slate-950/80 border border-slate-200/80 dark:border-slate-800/60 rounded-lg px-2.5 py-1.5">
        {/* Primary IP */}
        <div className="flex items-center justify-between text-xs min-w-0">
          <span className="font-mono text-[11px] font-semibold text-slate-900 dark:text-slate-200 truncate select-all">
            <span className="text-slate-600 font-sans font-semibold mr-1 dark:text-slate-500">P:</span>
            {dns.primary_ip}
          </span>
          <button
            type="button"
            onClick={() => copyToClipboard(dns.primary_ip, "primary")}
            title="Copy Primary IP"
            className="p-0.5 text-slate-500 hover:text-slate-800 hover:bg-slate-200/60 dark:text-slate-500 dark:hover:text-slate-200 dark:hover:bg-slate-800 rounded transition-colors shrink-0 ml-1"
          >
            {copiedField === "primary" ? (
              <Check className="w-3 h-3 text-emerald-500" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
          </button>
        </div>

        {/* Secondary IP */}
        <div className="flex items-center justify-between text-xs border-l border-slate-200 dark:border-slate-800/80 pl-2 min-w-0">
          <span className="font-mono text-[11px] font-semibold text-slate-900 dark:text-slate-200 truncate select-all">
            <span className="text-slate-600 font-sans font-semibold mr-1 dark:text-slate-500">S:</span>
            {dns.secondary_ip}
          </span>
          <button
            type="button"
            onClick={() => copyToClipboard(dns.secondary_ip, "secondary")}
            title="Copy Secondary IP"
            className="p-0.5 text-slate-500 hover:text-slate-800 hover:bg-slate-200/60 dark:text-slate-500 dark:hover:text-slate-200 dark:hover:bg-slate-800 rounded transition-colors shrink-0 ml-1"
          >
            {copiedField === "secondary" ? (
              <Check className="w-3 h-3 text-emerald-500" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
          </button>
        </div>
      </div>

      {/* Row 3 (Footer — Ping & Action) */}
      <div className="flex items-center justify-between gap-2 pt-0.5">
        {/* Left: Latency badge + small re-ping icon */}
        <div className="flex items-center gap-1.5">
          {renderLatencyBadge()}
          <button
            type="button"
            onClick={() => onPing(dns.id)}
            disabled={isPinging}
            title="Re-test latency"
            className="p-1 text-slate-400 hover:text-emerald-600 hover:bg-slate-100 dark:text-slate-500 dark:hover:text-emerald-400 dark:hover:bg-slate-800 rounded transition-all disabled:opacity-50"
          >
            <Activity className="w-3 h-3" />
          </button>
        </div>

        {/* Right: Compact Action Button */}
        {isActive ? (
          <span className="h-7 px-3 text-[11px] font-semibold rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-300 dark:bg-emerald-500/15 dark:text-emerald-400 dark:border-emerald-500/30 flex items-center gap-1 cursor-default shadow-xs">
            <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
            <span>Active ✓</span>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => onApply(dns)}
            disabled={isApplying}
            className={`h-7 px-3.5 text-xs font-semibold rounded-lg transition-all active:scale-95 shadow-sm flex items-center gap-1 ${
              isApplying
                ? "bg-indigo-600/60 text-white cursor-wait"
                : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-900/15"
            }`}
          >
            {isApplying ? (
              <span>Applying...</span>
            ) : (
              <>
                <span>Apply</span>
                <ArrowRight className="w-3 h-3" />
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};
