export function ToggleSwitch({ checked, onChange, label, disabled = false }) {
    return (
        <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative">
                <input
                    type="checkbox"
                    className="sr-only"
                    checked={checked}
                    onChange={(e) => onChange(e.target.checked)}
                    disabled={disabled}
                />
                <div
                    className={`block w-14 h-8 rounded-full transition-colors ${
                        checked ? 'bg-primary' : 'bg-slate-700'
                    } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                ></div>
                <div
                    className={`absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${
                        checked ? 'transform translate-x-6' : ''
                    }`}
                ></div>
            </div>
            {label && (
                <span className="text-sm text-slate-300">{label}</span>
            )}
        </label>
    );
}
