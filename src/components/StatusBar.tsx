import React from "react";
import {
  Wifi,
  Network,
  RotateCcw,
  Zap,
  ShieldAlert,
  Radio,
  Sliders,
  AlertTriangle,
  Globe,
} from "lucide-react";
import { ActiveNetworkInfo } from "../types";

interface StatusBarProps {
  network: ActiveNetworkInfo | null;
  isAdmin: boolean;
  captivePortalAlert: string | null;
  autoFlush: boolean;
  onToggleAutoFlush: () => void;
  onResetDhcp: () => void;
  onFlushCache: () => void;
  onOpenProfiles: () => void;
  loadingDhcp: boolean;
  loadingFlush: boolean;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  network,
  isAdmin,
  captivePortalAlert,
  autoFlush,
  onToggleAutoFlush,
  onResetDhcp,
  onFlushCache,
  onOpenProfiles,
  loadingDhcp,
  loadingFlush,
}) => {
  const isWifi = network?.connection_type === "Wi-Fi";
  const isConnected = network?.is_connected ?? false;
  const isDhcp = network?.dhcp_enabled ?? true;
  const currentDns = network?.current_dns ?? [];
  const vpnActive = network?.vpn_active ?? false;

  return (
    <div className="flex flex-col gap-1.5 shrink-0">
      {/* Admin Elevation Warning (Ultra-compact) */}
      {!isAdmin && (
        <div className="flex items-center justify-between px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-300 text-[11px] shadow-sm">
          <div className="flex items-center gap-1.5 truncate">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate">
              <strong>Standard Mode:</strong> Changing DNS requires Administrator rights. Run as Admin if needed.
            </span>
          </div>
          <span className="bg-amber-500/20 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-amber-300 shrink-0 ml-2">
            Limited
          </span>
        </div>
      )}

      {/* Captive Portal Alert (Ultra-compact) */}
      {captivePortalAlert && (
        <div className="flex items-center justify-between px-3 py-1 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-[11px] shadow-sm animate-pulse">
          <div className="flex items-center gap-1.5 truncate">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            <span className="truncate">{captivePortalAlert}</span>
          </div>
          <span className="bg-rose-500/20 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-rose-300 shrink-0 ml-2">
            DNS Held
          </span>
        </div>
      )}

      {/* Main Top Network Status Bar (Zero-wrap, High Density) */}
      <div className="bg-white border border-slate-200/90 rounded-xl py-2 px-3.5 flex items-center justify-between gap-3 shadow-md shadow-slate-900/[0.05] dark:bg-slate-900/80 dark:border-slate-800/90 dark:shadow-md backdrop-blur-md transition-colors">
        {/* Left Side: Adapter Icon + Network Name + Badges + Inline Active DNS */}
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center border shrink-0 transition-all ${
              isConnected
                ? "bg-emerald-50 border-emerald-300 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/30 dark:text-emerald-400"
                : "bg-slate-100 border-slate-300 text-slate-500 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-500"
            }`}
          >
            {isWifi ? <Wifi className="w-3.5 h-3.5" /> : <Network className="w-3.5 h-3.5" />}
          </div>

          <div className="flex items-center gap-2 min-w-0 flex-wrap sm:flex-nowrap">
            {/* SSID / Network Name */}
            <span className="font-bold text-xs text-slate-900 dark:text-slate-100 truncate max-w-[120px]" title={network?.network_identifier}>
              {network?.network_identifier || (network === null ? "Detecting Network..." : "No Connection")}
            </span>

            {/* Connection Type Badge */}
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold shrink-0 flex items-center gap-1 ${
                isConnected
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-300 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30"
                  : network === null
                  ? "bg-slate-100 text-slate-600 border border-slate-300 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700/60"
                  : "bg-rose-50 text-rose-800 border border-rose-300 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30"
              }`}
            >
              <span
                className={`w-1 h-1 rounded-full ${
                  isConnected
                    ? "bg-emerald-600 dark:bg-emerald-400 animate-pulse"
                    : network === null
                    ? "bg-amber-600 dark:bg-amber-400 animate-pulse"
                    : "bg-rose-600 dark:bg-rose-400"
                }`}
              />
              {isConnected
                ? isWifi
                  ? "Wi-Fi"
                  : "Ethernet"
                : network === null
                ? "Detecting..."
                : "Disconnected"}
            </span>

            {/* DNS Mode Badge: Static DNS vs DHCP */}
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold shrink-0 transition-all ${
                network === null
                  ? "bg-slate-100 text-slate-500 border border-slate-300 dark:bg-slate-800/60 dark:text-slate-500 dark:border-slate-700/40"
                  : isDhcp
                  ? "bg-blue-50 text-blue-800 border border-blue-300 dark:bg-blue-500/15 dark:text-blue-300 dark:border-blue-500/30"
                  : "bg-indigo-50 text-indigo-800 border border-indigo-300 shadow-xs dark:bg-indigo-500/20 dark:text-indigo-300 dark:border-indigo-500/40"
              }`}
            >
              {network === null ? "..." : isDhcp ? "DHCP" : "Static DNS"}
            </span>

            {/* VPN Active Badge */}
            {vpnActive && (
              <span
                title="VPN active: traffic and DNS queries route through the tunnel."
                className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-semibold bg-amber-50 text-amber-800 border border-amber-300 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/40 shrink-0"
              >
                <Globe className="w-2.5 h-2.5 text-amber-600 dark:text-amber-400" />
                <span>VPN</span>
              </span>
            )}

            {/* Inline Active DNS IPs */}
            <div className="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1 truncate shrink-0">
              <span className="text-slate-500 dark:text-slate-500 font-medium">Active:</span>
              {network === null ? (
                <span className="h-3 w-16 bg-slate-200/80 dark:bg-slate-800/80 rounded animate-pulse inline-block" />
              ) : currentDns.length > 0 ? (
                <span className="font-mono text-slate-900 dark:text-slate-200 bg-slate-100 dark:bg-slate-950/80 px-1.5 py-0.5 rounded text-[11px] font-semibold border border-slate-300 dark:border-slate-800/80 select-all">
                  {currentDns.join(", ")}
                </span>
              ) : (
                <span className="italic text-slate-500 dark:text-slate-500 text-[10px]">None</span>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Quick Action Controls (h-8) */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Auto-Flush Toggle Pill */}
          <button
            type="button"
            onClick={onToggleAutoFlush}
            title="Automatically flush Windows DNS cache upon changing DNS or DHCP"
            className={`h-7 flex items-center gap-1 px-2 rounded-lg text-[11px] font-semibold border transition-all ${
              autoFlush
                ? "bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-500/15 dark:border-emerald-500/40 dark:text-emerald-300 dark:hover:bg-emerald-500/25"
                : "bg-slate-100 border-slate-300 text-slate-700 hover:bg-slate-200/70 dark:bg-slate-800/80 dark:border-slate-700/80 dark:text-slate-400 dark:hover:bg-slate-700/80"
            }`}
          >
            <Zap className={`w-3 h-3 ${autoFlush ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400 dark:text-slate-500"}`} />
            <span>Auto-Flush</span>
          </button>

          {/* Manual Flush Button */}
          <button
            type="button"
            onClick={onFlushCache}
            disabled={loadingFlush}
            title="Flush Windows DNS resolver cache now"
            className="h-7 flex items-center gap-1 px-2.5 rounded-lg text-[11px] font-semibold bg-slate-100 hover:bg-slate-200/80 text-slate-800 border border-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 dark:border-slate-700/80 transition-all active:scale-95 disabled:opacity-50 shadow-xs"
          >
            <RotateCcw className={`w-3 h-3 ${loadingFlush ? "animate-spin text-indigo-500 dark:text-indigo-400" : "text-slate-500"}`} />
            <span>Flush</span>
          </button>

          {/* Reset to DHCP Button */}
          <button
            type="button"
            onClick={onResetDhcp}
            disabled={loadingDhcp || isDhcp}
            title={
              isDhcp
                ? "DNS is already obtained automatically via DHCP"
                : "Reset network adapter to obtain DNS automatically via DHCP"
            }
            className={`h-7 flex items-center gap-1 px-2.5 rounded-lg text-[11px] font-semibold border transition-all active:scale-95 disabled:opacity-40 disabled:pointer-events-none ${
              isDhcp
                ? "bg-slate-100 text-slate-400 border-slate-200 dark:bg-slate-800/60 dark:text-slate-500 dark:border-slate-700/40"
                : "bg-blue-50 hover:bg-blue-100 border-blue-300 text-blue-800 shadow-xs dark:bg-blue-600/30 dark:hover:bg-blue-600/45 dark:border-blue-500/50 dark:text-blue-200"
            }`}
          >
            <Radio className={`w-3 h-3 ${loadingDhcp ? "animate-spin" : ""}`} />
            <span>{loadingDhcp ? "Resetting..." : "Reset DHCP"}</span>
          </button>

          {/* Smart Profiles Drawer Button */}
          <button
            type="button"
            onClick={onOpenProfiles}
            title="Smart Network Profiles & Automation Rules"
            className="h-7 flex items-center gap-1 px-2.5 rounded-lg text-[11px] font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-800 border border-indigo-300 shadow-xs dark:bg-indigo-600/25 dark:hover:bg-indigo-600/40 dark:text-indigo-300 dark:border-indigo-500/40 transition-all active:scale-95"
          >
            <Sliders className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
            <span>Smart Profiles</span>
          </button>
        </div>
      </div>
    </div>
  );
};
