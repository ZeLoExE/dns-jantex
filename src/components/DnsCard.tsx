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
        <span className="flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 border border-indigo-500/40 text-indigo-300">
          <Activity className="w-2.5 h-2.5 animate-spin text-indigo-400" />
          <span>Testing...</span>
        </span>
      );
    }

    if (dns.latency_ms === null || dns.latency_ms === undefined) {
      return (
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-500">
          -- ms
        </span>
      );
    }

    if (dns.latency_ms === -1) {
      return (
        <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/40 text-rose-400">
          <WifiOff className="w-2.5 h-2.5 text-rose-400" />
          <span>Timeout</span>
        </span>
      );
    }

    const ms = dns.latency_ms;
    let badgeClass = "bg-emerald-500/15 border-emerald-500/30 text-emerald-300";
    if (ms > 100) {
      badgeClass = "bg-orange-500/15 border-orange-500/30 text-orange-400";
    } else if (ms >= 50) {
      badgeClass = "bg-amber-500/15 border-amber-500/30 text-amber-300";
    }

    return (
      <span
        className={`flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full border shadow-sm ${badgeClass}`}
      >
        <span className="w-1 h-1 rounded-full bg-current" />
        {ms} ms
      </span>
    );
  };

  return (
    <div
      className={`rounded-xl p-3 bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between gap-2.5 ${
        isActive
          ? "border-emerald-500/50 bg-emerald-950/15 shadow-sm shadow-emerald-950/20 ring-1 ring-emerald-500/30"
          : ""
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
            className="p-0.5 hover:bg-slate-800 rounded transition-all shrink-0"
          >
            <Star
              className={`w-3.5 h-3.5 transition-all ${
                dns.is_favorite
                  ? "fill-amber-400 text-amber-400 scale-105"
                  : "text-slate-600 hover:text-slate-400"
              }`}
            />
          </button>

          <span
            className="font-semibold text-xs text-slate-100 truncate"
            title={dns.name}
          >
            {dns.name}
          </span>

          {isActive && (
            <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shrink-0">
              ACTIVE
            </span>
          )}
        </div>

        {/* Right: Max 2 Compact Tags + Delete Icon */}
        <div className="flex items-center gap-1 shrink-0">
          {dns.tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/40 truncate max-w-[70px]"
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
              className="p-1 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded transition-colors"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Row 2 (IP Addresses — Compact Inline Box) */}
      <div className="grid grid-cols-2 gap-2 bg-slate-950/80 border border-slate-800/60 rounded-lg px-2.5 py-1.5">
        {/* Primary IP */}
        <div className="flex items-center justify-between text-xs min-w-0">
          <span className="font-mono text-[11px] text-slate-200 truncate select-all">
            <span className="text-slate-500 font-sans font-semibold mr-1">P:</span>
            {dns.primary_ip}
          </span>
          <button
            type="button"
            onClick={() => copyToClipboard(dns.primary_ip, "primary")}
            title="Copy Primary IP"
            className="p-0.5 text-slate-500 hover:text-slate-200 rounded transition-colors shrink-0 ml-1"
          >
            {copiedField === "primary" ? (
              <Check className="w-3 h-3 text-emerald-400" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
          </button>
        </div>

        {/* Secondary IP */}
        <div className="flex items-center justify-between text-xs border-l border-slate-800/80 pl-2 min-w-0">
          <span className="font-mono text-[11px] text-slate-200 truncate select-all">
            <span className="text-slate-500 font-sans font-semibold mr-1">S:</span>
            {dns.secondary_ip}
          </span>
          <button
            type="button"
            onClick={() => copyToClipboard(dns.secondary_ip, "secondary")}
            title="Copy Secondary IP"
            className="p-0.5 text-slate-500 hover:text-slate-200 rounded transition-colors shrink-0 ml-1"
          >
            {copiedField === "secondary" ? (
              <Check className="w-3 h-3 text-emerald-400" />
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
            className="p-1 text-slate-500 hover:text-emerald-400 hover:bg-slate-800 rounded transition-all disabled:opacity-50"
          >
            <Activity className="w-3 h-3" />
          </button>
        </div>

        {/* Right: Compact Action Button */}
        {isActive ? (
          <span className="h-7 px-3 text-[11px] font-semibold rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 cursor-default shadow-sm">
            <Check className="w-3 h-3 text-emerald-400" />
            <span>Active ✓</span>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => onApply(dns)}
            disabled={isApplying}
            className={`h-7 px-3.5 text-xs font-medium rounded-lg transition-all active:scale-95 shadow-sm flex items-center gap-1 ${
              isApplying
                ? "bg-indigo-600/60 text-white cursor-wait"
                : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-950/40"
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
