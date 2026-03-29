import { MaterialIcon } from './MaterialIcon.jsx';

export function BrandMark({ compact = false }) {
    const iconSize = compact ? 'size-6' : 'size-8';
    const textSize = compact ? 'text-sm' : 'text-xl';
    const wrapperTone = compact ? 'opacity-50 grayscale' : '';

    return (
        <div className={`flex items-center gap-3 ${wrapperTone}`.trim()}>
            <div className={`${iconSize} flex items-center justify-center rounded bg-primary`}>
                <MaterialIcon className={`${compact ? 'text-sm' : 'font-bold'} text-white`}>
                    segment
                </MaterialIcon>
            </div>
            <h2 className={`${textSize} font-bold tracking-tighter text-slate-100`}>
                FRAGMENT <span className="font-light text-primary">AI</span>
            </h2>
        </div>
    );
}
