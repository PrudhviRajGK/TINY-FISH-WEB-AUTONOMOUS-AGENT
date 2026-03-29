import { useState, useEffect } from 'react';
import { MaterialIcon } from '../../../components/ui/MaterialIcon.jsx';
import { ToggleSwitch } from '../../../components/ui/ToggleSwitch.jsx';
import { ProgressBar } from '../../../components/ui/ProgressBar.jsx';
import { 
    runAutomation, 
    getAutomationStatus, 
    getTrendingArticles 
} from '../../../services/automationApi.js';

export function AutomationPanel({ onAutomationComplete }) {
    const [isRunning, setIsRunning] = useState(false);
    const [autoPublish, setAutoPublish] = useState(false);
    const [topN, setTopN] = useState(3);
    const [language, setLanguage] = useState('en');
    const [trendingArticles, setTrendingArticles] = useState([]);
    const [isLoadingArticles, setIsLoadingArticles] = useState(false);
    const [statusMessage, setStatusMessage] = useState('');
    const [progress, setProgress] = useState(null);

    // Poll automation status
    useEffect(() => {
        let interval;
        
        if (isRunning) {
            interval = setInterval(async () => {
                try {
                    const status = await getAutomationStatus();
                    setIsRunning(status.is_running);
                    setProgress(status.progress);
                    
                    if (!status.is_running) {
                        setStatusMessage('Automation completed!');
                        clearInterval(interval);
                        
                        // Notify parent to refresh video library
                        if (onAutomationComplete) {
                            onAutomationComplete();
                        }
                    }
                } catch (error) {
                    console.error('Failed to get status:', error);
                }
            }, 3000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [isRunning, onAutomationComplete]);

    // Load trending articles on mount
    useEffect(() => {
        loadTrendingArticles();
    }, []);

    async function loadTrendingArticles() {
        setIsLoadingArticles(true);
        try {
            const articles = await getTrendingArticles(10);
            setTrendingArticles(articles);
        } catch (error) {
            console.error('Failed to load articles:', error);
            setStatusMessage('Failed to load trending articles');
        } finally {
            setIsLoadingArticles(false);
        }
    }

    async function handleRunAutomation() {
        try {
            setIsRunning(true);
            setStatusMessage('Starting automation...');
            
            // Get the URLs of the articles we're showing
            const selectedArticles = trendingArticles.slice(0, topN);
            const articleUrls = selectedArticles.map(article => article.url);
            
            await runAutomation({
                top_n: topN,
                auto_publish: autoPublish,
                article_urls: articleUrls,
                language,
            });
            
            setStatusMessage(`Processing ${topN} selected articles...`);
        } catch (error) {
            console.error('Automation failed:', error);
            setStatusMessage('Automation failed: ' + error.message);
            setIsRunning(false);
        }
    }

    return (
        <div className="rounded-2xl border border-border-dark bg-surface-dark p-6 shadow-sm">
            <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-yellow-500">
                        <MaterialIcon name="auto_awesome" className="text-white" />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-slate-100">
                            TinyFish Web Agent Automation
                        </h2>
                        <p className="text-sm text-slate-400">
                            AI agent navigates the web and converts trending news into viral videos
                        </p>
                    </div>
                </div>
                
                <button
                    onClick={loadTrendingArticles}
                    disabled={isLoadingArticles || isRunning}
                    className="flex items-center gap-2 rounded-lg border border-border-dark px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-surface-dark hover:text-white disabled:opacity-50"
                >
                    <MaterialIcon name="refresh" size={18} />
                    Refresh
                </button>
            </div>

            {/* Configuration */}
            <div className="mb-6 space-y-4 rounded-xl bg-background-dark/50 border border-border-dark p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <label className="text-sm font-medium text-slate-100">
                            Number of Articles
                        </label>
                        <p className="text-xs text-slate-400">
                            Process top N trending articles
                        </p>
                    </div>
                    <select
                        value={topN}
                        onChange={(e) => setTopN(Number(e.target.value))}
                        disabled={isRunning}
                        className="rounded-lg border border-border-dark bg-surface-dark px-3 py-2 text-sm font-medium text-slate-100 disabled:opacity-50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                        {[1, 2, 3, 4, 5].map((n) => (
                            <option key={n} value={n}>
                                {n} {n === 1 ? 'article' : 'articles'}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <label className="text-sm font-medium text-slate-100">
                            Auto-Publish
                        </label>
                        <p className="text-xs text-slate-400">
                            Automatically publish to YouTube
                        </p>
                    </div>
                    <ToggleSwitch
                        checked={autoPublish}
                        onChange={setAutoPublish}
                        disabled={isRunning}
                    />
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <label className="text-sm font-medium text-slate-100">
                            Language
                        </label>
                        <p className="text-xs text-slate-400">
                            Script, narration &amp; metadata language
                        </p>
                    </div>
                    <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        disabled={isRunning}
                        className="rounded-lg border border-border-dark bg-surface-dark px-3 py-2 text-sm font-medium text-slate-100 disabled:opacity-50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                        <option value="en">🇬🇧 English</option>
                        <option value="hi">🇮🇳 Hindi</option>
                        <option value="te">🇮🇳 Telugu</option>
                    </select>
                </div>
            </div>

            {/* Web Agent Activity */}
            {(isRunning || statusMessage) && (
                <div className="mb-6 rounded-xl border border-primary/30 bg-primary/10 p-4">
                    <div className="flex items-start gap-3">
                        <MaterialIcon
                            name={isRunning ? "travel_explore" : "check_circle"}
                            className={isRunning ? "text-primary animate-pulse" : "text-green-500"}
                        />
                        <div className="flex-1">
                            <p className="text-sm font-semibold text-slate-100 mb-2">
                                {isRunning ? 'Web Agent Activity' : statusMessage}
                            </p>
                            {isRunning && (
                                <ol className="space-y-1 text-xs text-slate-300">
                                    <li className="flex items-center gap-2">
                                        <MaterialIcon name="rss_feed" size={14} className="text-primary" />
                                        Step 1: RSS feeds fetching latest headlines
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <MaterialIcon name="trending_up" size={14} className="text-primary" />
                                        Step 2: Scoring articles by trend potential
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <MaterialIcon name="travel_explore" size={14} className="text-primary" />
                                        Step 3: TinyFish extracting full article content
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <MaterialIcon name="manage_search" size={14} className="text-primary" />
                                        Step 4: TinyFish detecting entities
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <MaterialIcon name="movie" size={14} className="text-primary" />
                                        Step 5: {progress || 'Generating video...'}
                                    </li>
                                </ol>
                            )}
                            {isRunning && (
                                <div className="mt-3">
                                    <ProgressBar progress={null} />
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Run Button */}
            <button
                onClick={handleRunAutomation}
                disabled={isRunning || isLoadingArticles}
                className="mb-6 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-6 py-3 font-semibold text-white shadow-lg transition-all hover:bg-yellow-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <MaterialIcon name="play_arrow" />
                {isRunning ? 'Running Automation...' : 'Run Automation'}
            </button>

            {/* Trending Articles */}
            <div>
                <h3 className="mb-3 text-sm font-semibold text-slate-100">
                    Top Trending Articles {trendingArticles.length > 0 && `(Showing top ${topN})`}
                </h3>
                
                {isLoadingArticles ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-border-dark border-t-primary" />
                    </div>
                ) : trendingArticles.length === 0 ? (
                    <div className="rounded-lg border border-border-dark bg-background-dark/30 p-4 text-center text-sm text-slate-400">
                        No articles loaded. Click Refresh to fetch latest articles.
                    </div>
                ) : (
                    <div className="space-y-2">
                        {trendingArticles.slice(0, topN).map((article, index) => (
                            <div
                                key={article.url}
                                className="rounded-lg border-2 border-primary bg-surface-dark p-3 transition-colors hover:border-primary hover:bg-surface-dark/80"
                            >
                                <div className="flex items-start gap-3">
                                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-yellow-500 text-sm font-bold text-white">
                                        {index + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-2">
                                            <h4 className="text-sm font-medium text-slate-100 line-clamp-2">
                                                {article.title}
                                            </h4>
                                            <span className="flex-shrink-0 rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary">
                                                Will Process
                                            </span>
                                        </div>
                                        {article.trend_score && (
                                            <div className="mt-1 flex items-center gap-2">
                                                <span className="text-xs font-medium text-primary">
                                                    Score: {article.trend_score.toFixed(1)}
                                                </span>
                                                <span className="text-xs text-slate-500">
                                                    {article.category}
                                                </span>
                                            </div>
                                        )}
                                        {article.matched_keywords && article.matched_keywords.length > 0 && (
                                            <div className="mt-2 flex flex-wrap gap-1">
                                                {article.matched_keywords.slice(0, 3).map((keyword) => (
                                                    <span
                                                        key={keyword}
                                                        className="rounded-full bg-primary/20 px-2 py-0.5 text-xs text-primary"
                                                    >
                                                        {keyword}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {trendingArticles.length > topN && (
                            <div className="rounded-lg border border-border-dark/50 bg-background-dark/30 p-3 text-center">
                                <p className="text-xs text-slate-500">
                                    +{trendingArticles.length - topN} more articles available
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
