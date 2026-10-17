import React from "react";

interface DnsCardSkeletonProps {
  index?: number;
}

export const DnsCardSkeleton: React.FC<DnsCardSkeletonProps> = ({ index = 0 }) => {
  // Realistic varying widths for server names
  const nameWidths = ["w-28", "w-36", "w-24", "w-32", "w-30", "w-28"];
  const nameWidth = nameWidths[index % nameWidths.length];

  // Tag placeholder variations
  const tagWidths = [
    ["w-12", "w-14"],
    ["w-14", "w-12"],
    ["w-16", "w-14"],
    ["w-12", "w-16"],
    ["w-14", "w-12"],
    ["w-12", "w-14"],
  ];
  const tags = tagWidths[index % tagWidths.length];

  return (
    <div
      className="animate-pulse bg-slate-200/60 dark:bg-slate-800/50 rounded-xl p-3 border border-slate-200/90 dark:border-slate-800/80 flex flex-col justify-between gap-2.5 select-none"
      aria-hidden="true"
    >
      {/* Row 1 (Header): Star + Title Placeholder + Tags Placeholder */}
      <div className="flex items-center justify-between gap-2">
        {/* Left: Star + Name placeholder */}
        <div className="flex items-center gap-1.5 min-w-0 flex-1">
          <div className="p-0.5 shrink-0">
            <div className="w-3.5 h-3.5 rounded bg-slate-300 dark:bg-slate-700/50" />
          </div>
          <div className={`h-3.5 ${nameWidth} rounded bg-slate-300 dark:bg-slate-700/60`} />
        </div>

        {/* Right: Tag placeholders */}
        <div className="flex items-center gap-1 shrink-0">
          {tags.map((tw, tIdx) => (
            <div
              key={tIdx}
              className={`h-4 ${tw} rounded bg-slate-200 dark:bg-slate-700/40 border border-slate-300/60 dark:border-slate-700/30`}
            />
          ))}
        </div>
      </div>

      {/* Row 2 (IP Addresses Box): Compact Inline Box */}
      <div className="grid grid-cols-2 gap-2 bg-slate-100 dark:bg-slate-950/80 border border-slate-200/80 dark:border-slate-800/60 rounded-lg px-2.5 py-1.5">
        {/* Primary IP column */}
        <div className="flex items-center justify-between text-xs min-w-0">
          <div className="flex items-center gap-1 min-w-0">
            <span className="text-slate-400 dark:text-slate-600 font-sans font-semibold text-xs select-none">P:</span>
            <div className="h-3 w-20 rounded bg-slate-300 dark:bg-slate-700/50" />
          </div>
          <div className="p-0.5 shrink-0 ml-1">
            <div className="w-3 h-3 rounded bg-slate-300 dark:bg-slate-700/40" />
          </div>
        </div>

        {/* Secondary IP column */}
        <div className="flex items-center justify-between text-xs border-l border-slate-200 dark:border-slate-800/80 pl-2 min-w-0">
          <div className="flex items-center gap-1 min-w-0">
            <span className="text-slate-400 dark:text-slate-600 font-sans font-semibold text-xs select-none">S:</span>
            <div className="h-3 w-20 rounded bg-slate-300 dark:bg-slate-700/50" />
          </div>
          <div className="p-0.5 shrink-0 ml-1">
            <div className="w-3 h-3 rounded bg-slate-300 dark:bg-slate-700/40" />
          </div>
        </div>
      </div>

      {/* Row 3 (Footer): Latency badge + Action button */}
      <div className="flex items-center justify-between gap-2 pt-0.5">
        {/* Left: Latency badge + small ping button placeholder */}
        <div className="flex items-center gap-1.5">
          <div className="h-5 w-14 rounded-full bg-slate-200 dark:bg-slate-700/50 border border-slate-300 dark:border-slate-700/40" />
          <div className="p-1">
            <div className="w-3 h-3 rounded bg-slate-300 dark:bg-slate-700/40" />
          </div>
        </div>

        {/* Right: Compact Action Button placeholder */}
        <div className="h-7 w-20 rounded-lg bg-indigo-500/20 dark:bg-indigo-600/30 border border-indigo-400/30 dark:border-indigo-500/20" />
      </div>
    </div>
  );
};

export default DnsCardSkeleton;
