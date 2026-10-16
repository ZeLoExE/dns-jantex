import React from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { Shield, Minus, X, Sparkles } from "lucide-react";
import { UpdateInfo } from "../types";

interface TitleBarProps {
  updateInfo?: UpdateInfo | null;
  onUpdateNow?: () => void;
  onDismissUpdate?: () => void;
}

export const TitleBar: React.FC<TitleBarProps> = ({
  updateInfo,
  onUpdateNow,
  onDismissUpdate,
}) => {
  const appWindow = getCurrentWindow();

  const handleMinimize = async () => {
    try {
      await appWindow.minimize();
    } catch (err) {
      console.error("Failed to minimize window:", err);
    }
  };

  const handleClose = async () => {
    try {
      await appWindow.close();
    } catch (err) {
      console.error("Failed to close window:", err);
    }
  };

  return (
    <header
      data-tauri-drag-region
      className="h-10 shrink-0 bg-[#0b0f19] border-b border-slate-800/80 flex items-center justify-between select-none px-3.5 z-50"
    >
      {/* Left: App Branding & Version */}
      <div data-tauri-drag-region className="flex items-center gap-2.5">
        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-indigo-500 to-emerald-500 flex items-center justify-center shadow-sm shadow-indigo-500/20">
          <Shield className="w-3.5 h-3.5 text-white" />
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold tracking-wide text-slate-100">
            DNS Jantex
          </span>
          <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-md bg-slate-800/90 text-slate-400 border border-slate-700/50 leading-none">
            v4.0.0
          </span>
        </div>
      </div>

      {/* Middle: Compact Glowing Update Pill (if available) or Drag Area */}
      <div data-tauri-drag-region className="flex-1 flex items-center justify-center h-full px-2">
        {updateInfo && (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-200 text-xs shadow-sm">
            <Sparkles className="w-3 h-3 text-indigo-400 shrink-0 animate-pulse" />
            <span className="font-medium text-[11px]">
              Update <strong className="text-white">{updateInfo.latest_version}</strong> Available
            </span>
            <span className="text-slate-600">·</span>
            <button
              type="button"
              onClick={onUpdateNow}
              className="text-emerald-400 hover:text-emerald-300 font-semibold text-[11px] underline underline-offset-2 transition-colors cursor-pointer"
            >
              Install
            </button>
            <button
              type="button"
              onClick={onDismissUpdate}
              title="Dismiss update"
              aria-label="Dismiss update"
              className="text-slate-500 hover:text-slate-300 ml-0.5 p-0.5 rounded hover:bg-slate-800/50 transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Right: Window Controls */}
      <div className="flex items-center -mr-3.5 h-full">
        <button
          type="button"
          onClick={handleMinimize}
          title="Minimize"
          aria-label="Minimize Window"
          className="h-10 w-11 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={handleClose}
          title="Close (Hide to Tray)"
          aria-label="Close Window"
          className="h-10 w-11 flex items-center justify-center text-slate-400 hover:text-white hover:bg-red-500/90 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
