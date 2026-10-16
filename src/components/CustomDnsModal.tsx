import React, { useState } from "react";
import { X, Plus, Zap, AlertCircle } from "lucide-react";
import { DnsServer } from "../types";

interface CustomDnsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (server: DnsServer, applyNow: boolean) => void;
}

const IPV4_REGEX =
  /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

export const CustomDnsModal: React.FC<CustomDnsModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState("");
  const [primaryIp, setPrimaryIp] = useState("");
  const [secondaryIp, setSecondaryIp] = useState("");
  const [tags, setTags] = useState("Custom");
  const [isFavorite, setIsFavorite] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (applyNow: boolean) => {
    setError(null);
    const trimmedName = name.trim();
    const trimmedPrimary = primaryIp.trim();
    const trimmedSecondary = secondaryIp.trim();

    if (!trimmedName) {
      setError("Please provide a name for this DNS server.");
      return;
    }

    if (!IPV4_REGEX.test(trimmedPrimary)) {
      setError("Primary IP must be a valid IPv4 address (e.g. 1.1.1.1).");
      return;
    }

    if (trimmedSecondary && !IPV4_REGEX.test(trimmedSecondary)) {
      setError("Secondary IP must be a valid IPv4 address or left blank.");
      return;
    }

    const tagList = tags
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const newDns: DnsServer = {
      id: "custom_" + Date.now(),
      name: trimmedName,
      primary_ip: trimmedPrimary,
      secondary_ip: trimmedSecondary,
      tags: tagList.length > 0 ? tagList : ["Custom"],
      is_favorite: isFavorite,
      latency_ms: null,
    };

    onSave(newDns, applyNow);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="glass-panel w-full max-w-md rounded-2xl p-5 shadow-2xl border border-slate-700/80 bg-slate-900/95 flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Plus className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-slate-100">
              Add Custom DNS Server
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Validation Error */}
        {error && (
          <div className="flex items-center gap-2 p-2.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Inputs Form */}
        <div className="flex flex-col gap-3 text-xs">
          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Server Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. My Fast Gaming DNS"
              className="w-full px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Primary IPv4 *
              </label>
              <input
                type="text"
                value={primaryIp}
                onChange={(e) => setPrimaryIp(e.target.value)}
                placeholder="1.1.1.1"
                className="w-full font-mono px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Secondary IPv4 (Optional)
              </label>
              <input
                type="text"
                value={secondaryIp}
                onChange={(e) => setSecondaryIp(e.target.value)}
                placeholder="1.0.0.1"
                className="w-full font-mono px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Category Tags (comma separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Custom, Gaming, Work"
              className="w-full px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="fav-check"
              checked={isFavorite}
              onChange={(e) => setIsFavorite(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="fav-check" className="text-slate-300 cursor-pointer">
              Pin to Favorites ⭐
            </label>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={() => handleSubmit(false)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all active:scale-95 shadow-sm"
          >
            Save to List
          </button>
          <button
            onClick={() => handleSubmit(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-all active:scale-95 shadow-sm shadow-emerald-900/30"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Apply Now</span>
          </button>
        </div>
      </div>
    </div>
  );
};
