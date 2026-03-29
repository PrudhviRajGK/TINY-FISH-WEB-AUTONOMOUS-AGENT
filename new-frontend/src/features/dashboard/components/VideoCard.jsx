import { MaterialIcon } from '../../../components/ui/MaterialIcon.jsx';
import { useState } from 'react';

export function VideoCard({ card, hasSearchQuery = false, isMatch = true, viewMode = 'grid' }) {
    const [isPlaying, setIsPlaying] = useState(false);

    const searchStateClasses = hasSearchQuery
        ? isMatch
            ? 'ring-1 ring-primary/60 shadow-[0_0_24px_rgba(139,0,0,0.18)]'
            : 'opacity-35 saturate-50'
        : '';

    const containerClasses =
        viewMode === 'list'
            ? `group flex cursor-pointer gap-4 rounded-lg border border-border-dark bg-surface-dark p-3 transition-all ${searchStateClasses}`.trim()
            : `group flex cursor-pointer flex-col transition-all ${searchStateClasses}`.trim();

    const thumbnailClasses =
        viewMode === 'list'
            ? 'relative aspect-video w-56 shrink-0 overflow-hidden rounded-lg border border-border-dark bg-surface-dark'
            : 'relative aspect-video overflow-hidden rounded-lg border border-border-dark bg-surface-dark';

    function handlePlayClick(e) {
        e.preventDefault();
        setIsPlaying(true);
    }

    function handleVideoClick(e) {
        e.stopPropagation();
    }

    return (
        <article className={containerClasses}>
            <div className={thumbnailClasses} onClick={!isPlaying ? handlePlayClick : undefined}>
                {isPlaying ? (
                    <video
                        className="absolute inset-0 h-full w-full object-cover"
                        controls
                        autoPlay
                        onClick={handleVideoClick}
                    >
                        <source src={card.href} type="video/mp4" />
                        Your browser does not support the video tag.
                    </video>
                ) : (
                    <>
                        <div
                            className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
                            style={{ 
                                background: card.imageUrl.startsWith('linear-gradient') 
                                    ? card.imageUrl 
                                    : `url('${card.imageUrl}')`,
                                backgroundSize: 'cover',
                                backgroundPosition: 'center'
                            }}
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-background-dark/90 to-transparent" />
                        {hasSearchQuery && isMatch ? (
                            <div className="absolute left-3 top-3 rounded-full border border-primary/35 bg-primary/15 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-primary">
                                Match
                            </div>
                        ) : null}
                        <div className="absolute bottom-3 right-3 rounded bg-black/80 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-white">
                            {card.durationLabel}
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100">
                            <div className="flex size-12 items-center justify-center rounded-full bg-primary text-white">
                                <MaterialIcon className="fill-1">play_arrow</MaterialIcon>
                            </div>
                        </div>
                    </>
                )}
            </div>

            <div className={viewMode === 'list' ? 'flex flex-1 items-start justify-between' : 'mt-4 flex items-start justify-between'}>
                <div>
                    <h4 className="text-sm font-bold tracking-tight text-slate-100 transition-colors group-hover:text-primary">
                        {isPlaying ? (
                            <span>{card.title}</span>
                        ) : (
                            <a href={card.href} rel="noreferrer" target="_blank">
                                {card.title}
                            </a>
                        )}
                    </h4>
                    <p className="mt-1 text-[10px] uppercase tracking-widest text-slate-500">
                        {card.meta}
                    </p>
                </div>
                <button className="text-primary transition-colors hover:text-white" type="button">
                    <MaterialIcon className="text-xl">more_vert</MaterialIcon>
                </button>
            </div>
        </article>
    );
}
