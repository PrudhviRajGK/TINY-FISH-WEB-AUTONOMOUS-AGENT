export function ProgressBar({ progress, label, showPercentage = true }) {
    return (
        <div className="w-full">
            {label && (
                <div className="flex justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                        {label}
                    </span>
                    {showPercentage && (
                        <span className="text-xs font-bold text-primary">
                            {Math.round(progress)}%
                        </span>
                    )}
                </div>
            )}
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                    className="bg-primary h-full transition-all duration-300 ease-out"
                    style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                ></div>
            </div>
        </div>
    );
}
