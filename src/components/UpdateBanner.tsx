import React from "react";
import { Download, Sparkles, X, ExternalLink } from "lucide-react";
import { UpdateInfo } from "../types";

interface UpdateBannerProps {
  updateInfo: UpdateInfo;
  onUpdateNow: () => void;
  onSkipVersion: () => void;
  onDismiss: () => void;
}

export const UpdateBanner: React.FC<UpdateBannerProps> = ({
  updateInfo,
  onUpdateNow,
  onSkipVersion,
  onDismiss,
}) => {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-r from-indigo-950/80 via-purple-950/70 to-slate-900 border border-indigo-500/40 rounded-xl shadow-lg text-xs animate-in slide-in-from-top-2 duration-200">
      <div className="flex items-center gap-2.5">
        <div className="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
          <Sparkles className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="font-semibold text-slate-100">
            DNS Jantex v{updateInfo.latest_version} is available!
          </span>
          <span className="text-slate-400 ml-2">
            (Current: v{updateInfo.current_version})
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onSkipVersion}
          title="Don't notify me again for this specific version"
          className="px-2.5 py-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-all"
        >
          Skip Version
        </button>

        <button
          onClick={onUpdateNow}
          className="flex items-center gap-1.5 px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow-sm transition-all active:scale-95"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Update Now</span>
          <ExternalLink className="w-3 h-3 opacity-70" />
        </button>

        <button
          onClick={onDismiss}
          className="p-1 text-slate-400 hover:text-slate-200 rounded-lg"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
