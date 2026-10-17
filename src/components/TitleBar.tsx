import React from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { Minus, X, Sparkles, Sun, Moon, Loader2 } from "lucide-react";
import { UpdateInfo } from "../types";
import appIconDark from "../../assets/icon.png";
import appIconLight from "../../assets/icon-light.png";

interface TitleBarProps {
  updateInfo?: UpdateInfo | null;
  onUpdateNow?: () => void;
  onDismissUpdate?: () => void;
  isUpdating?: boolean;
  updateStatus?: string;
  theme?: "dark" | "light";
  onToggleTheme?: () => void;
}

export const TitleBar: React.FC<TitleBarProps> = ({
  updateInfo,
  onUpdateNow,
  onDismissUpdate,
  isUpdating = false,
  updateStatus = "Downloading Update...",
  theme = "dark",
  onToggleTheme,
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
      className="h-10 shrink-0 bg-white/90 dark:bg-[#0b0f19] border-b border-slate-200/90 dark:border-slate-800/80 flex items-center justify-between select-none px-3.5 z-50 transition-colors backdrop-blur-md"
    >
      {/* Left: App Branding with 3D Violet J Icon & Version */}
      <div data-tauri-drag-region className="flex items-center gap-2.5">
        <div className="w-5 h-5 rounded-md flex items-center justify-center shrink-0 drop-shadow-sm">
          <img
            src={theme === "light" ? appIconLight : appIconDark}
            alt="DNS Jantex"
            className="w-full h-full object-contain"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold tracking-wide text-slate-900 dark:text-slate-100">
            DNS Jantex
          </span>
          <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800/90 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50 leading-none">
            v4.0.2
          </span>
        </div>
      </div>

      {/* Middle: Compact Glowing Update Pill (if available) or Drag Area */}
      <div data-tauri-drag-region className="flex-1 flex items-center justify-center h-full px-2">
        {updateInfo && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-700 dark:text-indigo-200 text-xs shadow-sm">
            {isUpdating ? (
              <Loader2 className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 shrink-0 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400 shrink-0 animate-pulse" />
            )}
            <span className="font-medium text-[11px]">
              {isUpdating ? (
                <span>{updateStatus}</span>
              ) : (
                <>
                  Update <strong className="text-slate-900 dark:text-white">v{updateInfo.latest_version}</strong> Available
                </>
              )}
            </span>
            {!isUpdating && (
              <>
                <span className="text-slate-400 dark:text-slate-600">·</span>
                <button
                  type="button"
                  onClick={onUpdateNow}
                  className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 dark:hover:text-emerald-300 font-bold text-[11px] underline underline-offset-2 transition-colors cursor-pointer"
                >
                  Update Now
                </button>
                <button
                  type="button"
                  onClick={onDismissUpdate}
                  title="Dismiss update"
                  aria-label="Dismiss update"
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 ml-0.5 p-0.5 rounded hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Right: Window Controls */}
      <div className="flex items-center -mr-3.5 h-full">
        {onToggleTheme && (
          <button
            type="button"
            onClick={onToggleTheme}
            title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
            aria-label={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
            className="h-10 w-10 flex items-center justify-center text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-amber-300 dark:hover:bg-slate-800 transition-colors"
          >
            {theme === "light" ? (
              <Moon className="w-4 h-4 text-slate-700 hover:text-indigo-600 transition-colors" />
            ) : (
              <Sun className="w-4 h-4 text-amber-400 hover:text-amber-300 transition-colors" />
            )}
          </button>
        )}

        <button
          type="button"
          onClick={handleMinimize}
          title="Minimize"
          aria-label="Minimize Window"
          className="h-10 w-11 flex items-center justify-center text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800 transition-colors"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={handleClose}
          title="Close (Hide to Tray)"
          aria-label="Close Window"
          className="h-10 w-11 flex items-center justify-center text-slate-500 hover:text-white hover:bg-red-500 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
