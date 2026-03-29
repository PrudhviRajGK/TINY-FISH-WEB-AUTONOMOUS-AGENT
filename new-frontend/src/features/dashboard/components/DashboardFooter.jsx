import { BrandMark } from '../../../components/ui/BrandMark.jsx';

export function DashboardFooter() {
    return (
        <footer className="border-t border-border-dark bg-background-dark/90 px-6 py-8 backdrop-blur-md">
            <div className="mx-auto max-w-7xl rounded-2xl border border-border-dark bg-surface-dark/70 px-6 py-6">
                <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
                    <div className="flex flex-col gap-4 md:flex-row md:items-center">
                        <BrandMark compact />
                        <div className="hidden h-6 w-px bg-border-dark md:block" />
                        <p className="max-w-xl text-sm leading-relaxed text-slate-500">
                            A modern workspace for creating, tracking, and reviewing AI-generated educational videos.
                        </p>
                    </div>

                    <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">
                        &copy; 2026 Fragment AI. All rights reserved.
                    </p>
                </div>
            </div>
        </footer>
    );
}
