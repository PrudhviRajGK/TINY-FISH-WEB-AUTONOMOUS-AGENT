import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { DashboardHeader } from './DashboardHeader.jsx';
import { DashboardHero } from './DashboardHero.jsx';
import { GenerationPanel } from './GenerationPanel.jsx';
import { AutomationPanel } from './AutomationPanel.jsx';
import { PipelineSection } from './PipelineSection.jsx';
import { VideoLibrarySection } from './VideoLibrarySection.jsx';
import { pipelineSteps } from '../constants/pipelineSteps.js';
import { buildLibraryCards } from '../lib/buildLibraryCards.js';
import { buildPipelineStepStates } from '../lib/buildPipelineStepStates.js';
import { buildVideoPayload } from '../lib/buildVideoPayload.js';
import { matchesLibraryCard } from '../lib/matchesLibraryCard.js';
import { generateVideo, listVideos } from '../../../services/videoApi.js';

export function DashboardPage() {
    const [activeSection, setActiveSection] = useState('dashboard-section');
    const [videos, setVideos] = useState([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isPollingLibrary, setIsPollingLibrary] = useState(false);
    const [pipelineState, setPipelineState] = useState({
        mode: 'idle',
        activeStepKey: null,
        statusText: 'Ready to render',
    });
    const [searchQuery, setSearchQuery] = useState('');
    const pollingTimerRef = useRef(null);
    const pipelineTimerRef = useRef(null);
    const pendingSearchScrollYRef = useRef(null);
    const trackedVideoFilenameRef = useRef(null);

    const libraryCards = buildLibraryCards(videos, trackedVideoFilenameRef.current);
    const normalizedSearchQuery = searchQuery.trim().toLowerCase();
    const matchingCardIds = new Set(
        normalizedSearchQuery
            ? libraryCards
                  .filter((card) => matchesLibraryCard(card, normalizedSearchQuery))
                  .map((card) => card.id)
            : libraryCards.map((card) => card.id)
    );
    const matchCount = normalizedSearchQuery ? matchingCardIds.size : libraryCards.length;
    const pipelineStepStates = buildPipelineStepStates(
        pipelineState.mode,
        pipelineState.activeStepKey
    );
    const showAwaitingCard = isGenerating || libraryCards.length < 4;

    useLayoutEffect(() => {
        if (pendingSearchScrollYRef.current === null) {
            return undefined;
        }

        const lockedScrollY = pendingSearchScrollYRef.current;
        pendingSearchScrollYRef.current = null;
        let nextFrameId = 0;
        let finalFrameId = 0;

        const restoreScrollPosition = () => {
            window.scrollTo({
                top: lockedScrollY,
                behavior: 'auto',
            });
        };

        restoreScrollPosition();

        nextFrameId = window.requestAnimationFrame(() => {
            restoreScrollPosition();
            finalFrameId = window.requestAnimationFrame(restoreScrollPosition);
        });

        return () => {
            window.cancelAnimationFrame(nextFrameId);
            window.cancelAnimationFrame(finalFrameId);
        };
    }, [searchQuery, libraryCards.length, showAwaitingCard]);

    const refreshLibrary = useCallback(async (options = {}) => {
        const { preserveRenderStatus = false } = options;

        try {
            const response = await listVideos();
            setVideos(response);

            if (!preserveRenderStatus) {
                setPipelineState((currentState) =>
                    currentState.mode === 'running'
                        ? currentState
                        : {
                              mode: 'idle',
                              activeStepKey: null,
                              statusText: response.length ? 'Library synced' : 'Ready to render',
                          }
                );
            }

            return response;
        } catch {
            setVideos([]);

            if (!preserveRenderStatus) {
                setPipelineState((currentState) =>
                    currentState.mode === 'running'
                        ? currentState
                        : {
                              mode: 'idle',
                              activeStepKey: null,
                              statusText: 'Ready to render',
                          }
                );
            }

            return [];
        }
    }, []);

    useEffect(() => {
        void refreshLibrary();

        return () => {
            if (pollingTimerRef.current) {
                window.clearInterval(pollingTimerRef.current);
            }

            if (pipelineTimerRef.current) {
                window.clearTimeout(pipelineTimerRef.current);
            }
        };
    }, [refreshLibrary]);

    useEffect(() => {
        const sectionIds = [
            'dashboard-section',
            'pipeline-section',
            'generation-panel',
            'library-section',
        ];

        const sections = sectionIds
            .map((sectionId) => document.getElementById(sectionId))
            .filter(Boolean);

        if (!sections.length) {
            return undefined;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const visibleEntry = entries
                    .filter((entry) => entry.isIntersecting)
                    .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

                if (visibleEntry?.target?.id) {
                    setActiveSection(visibleEntry.target.id);
                }
            },
            {
                rootMargin: '-30% 0px -45% 0px',
                threshold: [0.2, 0.4, 0.6],
            }
        );

        sections.forEach((section) => observer.observe(section));

        return () => observer.disconnect();
    }, []);

    function clearPipelineTimer() {
        if (pipelineTimerRef.current) {
            window.clearTimeout(pipelineTimerRef.current);
            pipelineTimerRef.current = null;
        }
    }

    function markPipelineComplete() {
        clearPipelineTimer();

        setPipelineState({
            mode: 'complete',
            activeStepKey: null,
            statusText: 'Video ready',
        });

        if (pollingTimerRef.current) {
            window.clearInterval(pollingTimerRef.current);
            pollingTimerRef.current = null;
        }

        setIsPollingLibrary(false);
        scrollToSection('library-section');
    }

    function startPipelineSimulation(stepIndex = 0) {
        clearPipelineTimer();

        const step = pipelineSteps[stepIndex];

        if (!step) {
            return;
        }

        setPipelineState({
            mode: 'running',
            activeStepKey: step.key,
            statusText: step.statusText,
        });

        if (stepIndex >= pipelineSteps.length - 1) {
            return;
        }

        pipelineTimerRef.current = window.setTimeout(() => {
            startPipelineSimulation(stepIndex + 1);
        }, step.durationMs);
    }

    function startPolling(videoFilename) {
        if (pollingTimerRef.current) {
            window.clearInterval(pollingTimerRef.current);
        }

        setIsPollingLibrary(true);

        let attempts = 0;

        pollingTimerRef.current = window.setInterval(async () => {
            attempts += 1;
            const refreshedVideos = await refreshLibrary({ preserveRenderStatus: true });

            const isTargetReady = videoFilename
                ? refreshedVideos.some((video) => video.name === videoFilename)
                : false;

            if (isTargetReady) {
                markPipelineComplete();
                return;
            }

            if (attempts >= 120) {
                // Stop after 120 attempts (10 minutes)
                window.clearInterval(pollingTimerRef.current);
                pollingTimerRef.current = null;
                setIsPollingLibrary(false);
                await refreshLibrary({ preserveRenderStatus: false });
                scrollToSection('library-section');
            }
        }, 5000);
    }

    async function handleGenerate(formValues) {
        setIsGenerating(true);
        trackedVideoFilenameRef.current = null;
        startPipelineSimulation(0);

        try {
            const payload = buildVideoPayload(formValues);
            const response = await generateVideo(payload);
            trackedVideoFilenameRef.current = response.video_filename ?? null;
            await refreshLibrary({ preserveRenderStatus: true });
            startPolling(trackedVideoFilenameRef.current);
        } catch (error) {
            clearPipelineTimer();
            setPipelineState({
                mode: 'error',
                activeStepKey: pipelineState.activeStepKey ?? pipelineSteps[0].key,
                statusText: 'Render request failed',
            });
            throw error;
        } finally {
            setIsGenerating(false);
        }
    }

    function scrollToSection(sectionId) {
        document.getElementById(sectionId)?.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
        });
    }

    function handleSearchChange(value) {
        pendingSearchScrollYRef.current = window.scrollY;
        setSearchQuery(value);
    }

    return (
        <div className="relative flex min-h-screen w-full flex-col">
            <DashboardHeader
                activeSection={activeSection}
                onSearchChange={handleSearchChange}
                searchQuery={searchQuery}
            />

            <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-12 p-6 lg:p-10">
                <DashboardHero
                    onPreviewShowcase={() => scrollToSection('hero-showcase')}
                    onStartCreating={() => scrollToSection('generation-panel')}
                />

                <PipelineSection statusText={pipelineState.statusText} steps={pipelineStepStates} />

                <div className="grid gap-8 lg:grid-cols-3">
                    {/* Temporarily hidden for hackathon demo - focus on automation
                    <div className="lg:col-span-2">
                        <GenerationPanel
                            isGenerating={isGenerating}
                            onGenerate={handleGenerate}
                        />
                    </div>
                    */}
                    <div className="lg:col-span-3">
                        <AutomationPanel onAutomationComplete={() => refreshLibrary()} />
                    </div>
                </div>

                <VideoLibrarySection
                    cards={libraryCards}
                    isPolling={isPollingLibrary}
                    matchCount={matchCount}
                    matchingCardIds={matchingCardIds}
                    searchQuery={searchQuery}
                    showAwaitingCard={showAwaitingCard}
                />
            </main>
        </div>
    );
}
