import { MaterialIcon } from '../../../components/ui/MaterialIcon.jsx';
import { VideoCard } from './VideoCard.jsx';

export function VideoLibrarySection({
    cards,
    isPolling,
    matchCount,
    matchingCardIds,
    searchQuery,
    showAwaitingCard,
}) {
    const hasSearchQuery = Boolean(searchQuery.trim());
    const subtitle = hasSearchQuery
        ? matchCount
            ? `Found ${matchCount} matching video${matchCount === 1 ? '' : 's'} for "${searchQuery}"`
            : `No videos found for "${searchQuery}" in the Generated News Videos section.`
        : isPolling
          ? 'The library is auto-refreshing while automation is running'
          : 'AI-generated videos from Economic Times articles will appear here automatically';

    return (
        <section className="scroll-mt-32 flex flex-col gap-8" id="library-section">
            <div className="flex flex-col gap-4 border-b border-border-dark pb-4">
                <div className="flex flex-col gap-1">
                    <h3 className="flex items-center gap-3 text-2xl font-bold tracking-tight">
                        <MaterialIcon className="text-primary">video_library</MaterialIcon>
                        Generated News Videos
                    </h3>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                        {subtitle}
                    </p>
                </div>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {cards.map((card) => (
                    <VideoCard
                        card={card}
                        hasSearchQuery={hasSearchQuery}
                        isMatch={!hasSearchQuery || matchingCardIds.has(card.id)}
                        key={card.id}
                        viewMode="grid"
                    />
                ))}

                {showAwaitingCard ? (
                    <div className="flex aspect-video flex-col items-center justify-center rounded-lg border border-dashed border-border-dark bg-background-dark/30">
                        <MaterialIcon className="mb-2 text-4xl text-slate-700">
                            add_circle
                        </MaterialIcon>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-600">
                            Awaiting Output
                        </p>
                    </div>
                ) : null}
            </div>
        </section>
    );
}
