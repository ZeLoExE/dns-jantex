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
      <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl py-2 px-3.5 flex items-center justify-between gap-3 shadow-md backdrop-blur-md">
        {/* Left Side: Adapter Icon + Network Name + Badges + Inline Active DNS */}
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center border shrink-0 transition-all ${
              isConnected
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-slate-800 border-slate-700 text-slate-500"
            }`}
          >
            {isWifi ? <Wifi className="w-3.5 h-3.5" /> : <Network className="w-3.5 h-3.5" />}
          </div>

          <div className="flex items-center gap-2 min-w-0 flex-wrap sm:flex-nowrap">
            {/* SSID / Network Name */}
            <span className="font-semibold text-xs text-slate-100 truncate max-w-[120px]" title={network?.network_identifier}>
              {network?.network_identifier || "Searching Network..."}
            </span>

            {/* Connection Type Badge */}
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0 flex items-center gap-1 ${
                isConnected
                  ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                  : "bg-rose-500/15 text-rose-300 border border-rose-500/30"
              }`}
            >
              <span
                className={`w-1 h-1 rounded-full ${
                  isConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-400"
                }`}
              />
              {isConnected ? (isWifi ? "Wi-Fi" : "Ethernet") : "Disconnected"}
            </span>

            {/* DNS Mode Badge: Static DNS vs DHCP */}
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold shrink-0 transition-all ${
                isDhcp
                  ? "bg-blue-500/15 text-blue-300 border border-blue-500/30"
                  : "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm"
              }`}
            >
              {isDhcp ? "DHCP" : "Static DNS"}
            </span>

            {/* VPN Active Badge */}
            {vpnActive && (
              <span
                title="VPN active: traffic and DNS queries route through the tunnel."
                className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-amber-500/20 text-amber-300 border border-amber-500/40 shrink-0"
              >
                <Globe className="w-2.5 h-2.5 text-amber-400" />
                <span>VPN</span>
              </span>
            )}

            {/* Inline Active DNS IPs */}
            <div className="text-[11px] text-slate-400 flex items-center gap-1 truncate shrink-0">
              <span className="text-slate-500">Active:</span>
              {currentDns.length > 0 ? (
                <span className="font-mono text-slate-200 bg-slate-950/80 px-1.5 py-0.5 rounded text-[11px] border border-slate-800/80 select-all">
                  {currentDns.join(", ")}
                </span>
              ) : (
                <span className="italic text-slate-500 text-[10px]">None</span>
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
            className={`h-7 flex items-center gap-1 px-2 rounded-lg text-[11px] font-medium border transition-all ${
              autoFlush
                ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/25"
                : "bg-slate-800/80 border-slate-700/80 text-slate-400 hover:bg-slate-700/80"
            }`}
          >
            <Zap className={`w-3 h-3 ${autoFlush ? "text-emerald-400" : "text-slate-500"}`} />
            <span>Auto-Flush</span>
          </button>

          {/* Manual Flush Button */}
          <button
            type="button"
            onClick={onFlushCache}
            disabled={loadingFlush}
            title="Flush Windows DNS resolver cache now"
            className="h-7 flex items-center gap-1 px-2.5 rounded-lg text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition-all active:scale-95 disabled:opacity-50"
          >
            <RotateCcw className={`w-3 h-3 ${loadingFlush ? "animate-spin text-indigo-400" : "text-slate-400"}`} />
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
                ? "bg-slate-800/60 text-slate-500 border-slate-700/40"
                : "bg-blue-600/30 hover:bg-blue-600/45 border-blue-500/50 text-blue-200 shadow-sm"
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
            className="h-7 flex items-center gap-1 px-2.5 rounded-lg text-[11px] font-semibold bg-indigo-600/25 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/40 transition-all active:scale-95 shadow-sm"
          >
            <Sliders className="w-3 h-3 text-indigo-400" />
            <span>Smart Profiles</span>
          </button>
        </div>
      </div>
    </div>
  );
};
