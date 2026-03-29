import { MaterialIcon } from './MaterialIcon.jsx';

export function SearchField({ value, onChange }) {
    return (
        <div className="flex w-full justify-center lg:justify-end">
            <label className="group relative flex w-full max-w-xl items-center overflow-hidden rounded-full border border-primary/20 bg-surface-dark/90 px-4 py-3 shadow-[0_0_32px_rgba(139,0,0,0.16)] ring-1 ring-white/5 transition-all duration-200 focus-within:border-primary/60 focus-within:ring-primary/30">
                <MaterialIcon className="mr-3 text-lg text-primary">search</MaterialIcon>
                <input
                    className="w-full border-none bg-transparent p-0 text-sm text-slate-100 placeholder-slate-500 focus:ring-0"
                    onChange={(event) => onChange(event.target.value)}
                    placeholder="Search generated videos by topic..."
                    type="text"
                    value={value}
                />
                {value ? (
                    <button
                        className="ml-3 flex size-8 items-center justify-center rounded-full bg-primary/10 text-primary transition-colors hover:bg-primary/20"
                        onClick={(event) => {
                            event.preventDefault();
                            onChange('');
                        }}
                        type="button"
                    >
                        <MaterialIcon className="text-base">close</MaterialIcon>
                    </button>
                ) : (
                    <span className="ml-4 hidden rounded-full border border-primary/15 bg-primary/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary sm:inline-flex">
                        Video Search
                    </span>
                )}
            </label>
        </div>
    );
}
