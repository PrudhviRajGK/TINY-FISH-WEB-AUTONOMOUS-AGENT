export function Dropdown({ value, onChange, options, label, placeholder, disabled = false }) {
    return (
        <label className="flex flex-col gap-2">
            {label && (
                <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                    {label}
                </span>
            )}
            <select
                className="rounded border border-border-dark bg-background-dark p-4 text-slate-100 transition-all focus:border-primary focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
            >
                {placeholder && (
                    <option value="" disabled>
                        {placeholder}
                    </option>
                )}
                {options.map((option) => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
        </label>
    );
}
