import React, { useState } from "react";
import {
  X,
  Sliders,
  Shield,
  Wifi,
  Trash2,
  CheckCircle2,
  Plus,
} from "lucide-react";
import { DnsServer, NetworkProfile, AppSettings } from "../types";

interface ProfilesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentNetworkId: string;
  dnsList: DnsServer[];
  profiles: NetworkProfile[];
  settings: AppSettings;
  onSaveProfile: (profile: NetworkProfile) => void;
  onDeleteProfile: (id: string) => void;
  onUpdateSettings: (settings: AppSettings) => void;
}

export const ProfilesDrawer: React.FC<ProfilesDrawerProps> = ({
  isOpen,
  onClose,
  currentNetworkId,
  dnsList,
  profiles,
  settings,
  onSaveProfile,
  onDeleteProfile,
  onUpdateSettings,
}) => {
  const [selectedDnsForCurrent, setSelectedDnsForCurrent] = useState<string>("DHCP");

  if (!isOpen) return null;

  const currentRule = profiles.find(
    (p) => p.network_identifier === currentNetworkId
  );

  const handleBindCurrent = () => {
    if (!currentNetworkId || currentNetworkId === "No Connection") return;
    const newProfile: NetworkProfile = {
      id: "profile_" + Date.now(),
      network_identifier: currentNetworkId,
      dns_id: selectedDnsForCurrent,
      enabled: true,
    };
    onSaveProfile(newProfile);
  };

  const getDnsName = (dnsId: string) => {
    if (dnsId === "DHCP") return "DHCP (Automatic DNS)";
    const found = dnsList.find((d) => d.id === dnsId);
    return found ? found.name : "Custom DNS";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-md h-full bg-[#0f172a] border-l border-slate-700/80 p-5 shadow-2xl flex flex-col justify-between overflow-y-auto">
        <div className="flex flex-col gap-4">
          {/* Header */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
                <Sliders className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-100">
                  Smart Network Profiles
                </h2>
                <p className="text-xs text-slate-400">
                  Auto-switch DNS based on active Wi-Fi / Ethernet
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Bind Active Network */}
          <div className="glass-panel rounded-xl p-3.5 border border-indigo-500/30 bg-indigo-950/20 flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wifi className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-semibold text-indigo-200">
                  Active Network
                </span>
              </div>
              <span className="font-mono text-xs font-bold text-slate-100 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                {currentNetworkId}
              </span>
            </div>

            {currentRule ? (
              <div className="flex items-center justify-between text-xs pt-1">
                <span className="text-slate-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Bound to: <strong>{getDnsName(currentRule.dns_id)}</strong>
                </span>
                <button
                  onClick={() => onDeleteProfile(currentRule.id)}
                  className="text-rose-400 hover:text-rose-300 text-[11px] underline"
                >
                  Unbind
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 pt-1">
                <select
                  value={selectedDnsForCurrent}
                  onChange={(e) => setSelectedDnsForCurrent(e.target.value)}
                  className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="DHCP">DHCP (Automatic DNS)</option>
                  {dnsList.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.primary_ip})
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleBindCurrent}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm shrink-0 active:scale-95"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Bind</span>
                </button>
              </div>
            )}
          </div>

          {/* Global Smart Profile Rules Settings */}
          <div className="flex flex-col gap-2 pt-1">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Automation Rules
            </h3>

            {/* Auto Apply Profiles Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex flex-col pr-2">
                <span className="text-xs font-medium text-slate-200">
                  Auto-Apply Profiles
                </span>
                <span className="text-[11px] text-slate-400">
                  Automatically switch DNS when connected network changes
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.auto_apply_profiles}
                onChange={(e) =>
                  onUpdateSettings({
                    ...settings,
                    auto_apply_profiles: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500 cursor-pointer"
              />
            </div>

            {/* Captive Portal Protection Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex flex-col pr-2">
                <div className="flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-xs font-medium text-slate-200">
                    Captive Portal Guard
                  </span>
                </div>
                <span className="text-[11px] text-slate-400">
                  Pause custom DNS when a Wi-Fi login page is detected
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.captive_portal_guard}
                onChange={(e) =>
                  onUpdateSettings({
                    ...settings,
                    captive_portal_guard: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500 cursor-pointer"
              />
            </div>
          </div>

          {/* Saved Network Profiles List */}
          <div className="flex flex-col gap-2 pt-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Configured Network Rules ({profiles.length})
            </h3>

            {profiles.length === 0 ? (
              <div className="p-4 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-500">
                No network rules saved yet. Connect to a network and click "Bind" to save a rule.
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {profiles.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs"
                  >
                    <div className="flex flex-col">
                      <span className="font-semibold text-slate-200">
                        {p.network_identifier}
                      </span>
                      <span className="text-slate-400 text-[11px]">
                        Target: {getDnsName(p.dns_id)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={p.enabled}
                        onChange={(e) =>
                          onSaveProfile({ ...p, enabled: e.target.checked })
                        }
                        title="Enable or disable this rule"
                        className="rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500 cursor-pointer"
                      />
                      <button
                        onClick={() => onDeleteProfile(p.id)}
                        className="p-1 text-slate-500 hover:text-rose-400 transition-all"
                        title="Delete rule"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 text-center">
          <button
            onClick={onClose}
            className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
