import { BrandMark } from '../../../components/ui/BrandMark.jsx';
import { SearchField } from '../../../components/ui/SearchField.jsx';
import { navigationLinks } from '../constants/navigationLinks.js';

export function DashboardHeader({ activeSection, searchQuery, onSearchChange }) {
    return (
        <header className="sticky top-0 z-50 border-b border-border-dark bg-background-dark/80 px-6 py-4 backdrop-blur-md">
            <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="flex items-center gap-12">
                    <a href="#dashboard-section">
                        <BrandMark />
                    </a>
                    <nav className="hidden items-center gap-8 lg:flex">
                        {navigationLinks.map((link) => (
                            <a
                                className={
                                    link.sectionId === activeSection
                                        ? 'text-sm font-semibold tracking-wide text-primary'
                                        : 'text-sm font-medium text-slate-400 transition-colors hover:text-white'
                                }
                                href={link.href}
                                key={link.label}
                            >
                                {link.label}
                            </a>
                        ))}
                    </nav>
                </div>

                <div className="w-full xl:max-w-xl">
                    <SearchField onChange={onSearchChange} value={searchQuery} />
                </div>
            </div>
        </header>
    );
}
