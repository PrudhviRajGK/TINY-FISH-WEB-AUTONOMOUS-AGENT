import { useState } from 'react';
import { MaterialIcon } from '../../../components/ui/MaterialIcon.jsx';
import { ToggleSwitch } from '../../../components/ui/ToggleSwitch.jsx';
import { Dropdown } from '../../../components/ui/Dropdown.jsx';
import { durationOptions } from '../constants/durationOptions.js';
import { contentModes } from '../constants/contentModes.js';
import { voiceStyles } from '../constants/voiceStyles.js';

const initialForm = {
    inputMode: 'topic', // 'topic' or 'article'
    topic: '',
    articleUrl: '',
    contentMode: 'news',
    duration: durationOptions[0].value,
    keyPoints: '',
    enableSubtitles: true,
    voiceStyle: 'narrator_male',
    useTinyfish: false,
    publishTo: [],
};

const platforms = [
    { id: 'youtube', label: 'YouTube Shorts', icon: 'play_circle' },
    { id: 'instagram', label: 'Instagram Reels', icon: 'photo_camera' },
    { id: 'tiktok', label: 'TikTok', icon: 'music_note' },
    { id: 'linkedin', label: 'LinkedIn', icon: 'business' },
];

export function GenerationPanel({ isGenerating, onGenerate }) {
    const [formValues, setFormValues] = useState(initialForm);
    const [showPublishSettings, setShowPublishSettings] = useState(false);

    function handleChange(event) {
        const { name, value } = event.target;
        setFormValues((current) => ({
            ...current,
            [name]: value,
        }));
    }

    function handleToggle(name, value) {
        setFormValues((current) => ({
            ...current,
            [name]: value,
        }));
    }

    function handlePlatformToggle(platformId) {
        setFormValues((current) => {
            const publishTo = current.publishTo.includes(platformId)
                ? current.publishTo.filter((id) => id !== platformId)
                : [...current.publishTo, platformId];
            return { ...current, publishTo };
        });
    }

    function handleInputModeChange(mode) {
        setFormValues((current) => ({
            ...current,
            inputMode: mode,
            useTinyfish: mode === 'article',
        }));
    }

    async function handleSubmit(event) {
        event.preventDefault();
        try {
            await onGenerate(formValues);
            setFormValues(initialForm);
        } catch {
            // Keep current form values in place if the request fails.
        }
    }

    const selectedMode = contentModes.find((m) => m.value === formValues.contentMode);

    return (
        <section
            className="scroll-mt-32 flex flex-col gap-6 rounded-xl border border-border-dark bg-surface-dark p-8"
            id="generation-panel"
        >
            <div className="border-b border-border-dark pb-6">
                <h3 className="flex items-center gap-3 text-xl font-bold">
                    <MaterialIcon className="text-primary">psychology</MaterialIcon>
                    Generation Panel
                </h3>
            </div>

            <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
                {/* Input Mode Selector */}
                <div className="flex flex-col gap-4">
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                        Input Method
                    </span>
                    <div className="flex gap-4">
                        <button
                            type="button"
                            onClick={() => handleInputModeChange('topic')}
                            className={`flex-1 rounded-lg border-2 p-4 transition-all ${
                                formValues.inputMode === 'topic'
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border-dark hover:border-slate-600'
                            }`}
                        >
                            <MaterialIcon className="text-2xl mb-2">edit_note</MaterialIcon>
                            <div className="text-sm font-bold">Topic Input</div>
                            <div className="text-xs text-slate-400 mt-1">
                                Generate from a topic or idea
                            </div>
                        </button>
                        <button
                            type="button"
                            onClick={() => handleInputModeChange('article')}
                            className={`flex-1 rounded-lg border-2 p-4 transition-all ${
                                formValues.inputMode === 'article'
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border-dark hover:border-slate-600'
                            }`}
                        >
                            <MaterialIcon className="text-2xl mb-2">article</MaterialIcon>
                            <div className="text-sm font-bold">Article URL</div>
                            <div className="text-xs text-slate-400 mt-1">
                                Extract content from article
                            </div>
                        </button>
                    </div>
                </div>

                {/* Input Fields */}
                <div className="grid gap-6 md:grid-cols-2">
                    {formValues.inputMode === 'topic' ? (
                        <label className="flex flex-col gap-2 md:col-span-2">
                            <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                                Video Topic
                            </span>
                            <input
                                className="rounded border border-border-dark bg-background-dark p-4 text-slate-100 transition-all focus:border-primary focus:ring-primary"
                                name="topic"
                                onChange={handleChange}
                                placeholder="e.g. Quantum Physics Explained"
                                required
                                type="text"
                                value={formValues.topic}
                            />
                        </label>
                    ) : (
                        <label className="flex flex-col gap-2 md:col-span-2">
                            <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                                Article URL
                            </span>
                            <input
                                className="rounded border border-border-dark bg-background-dark p-4 text-slate-100 transition-all focus:border-primary focus:ring-primary"
                                name="articleUrl"
                                onChange={handleChange}
                                placeholder="https://example.com/article"
                                required
                                type="url"
                                value={formValues.articleUrl}
                            />
                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                <MaterialIcon className="text-sm">info</MaterialIcon>
                                TinyFish will extract content, images, and metadata
                            </div>
                        </label>
                    )}

                    {/* Content Mode */}
                    <div className="md:col-span-2">
                        <Dropdown
                            label="Content Mode"
                            value={formValues.contentMode}
                            onChange={(value) => handleChange({ target: { name: 'contentMode', value } })}
                            options={contentModes}
                        />
                        {selectedMode && (
                            <div className="mt-2 text-xs text-slate-400 flex items-start gap-2">
                                <MaterialIcon className="text-sm mt-0.5">lightbulb</MaterialIcon>
                                {selectedMode.description}
                            </div>
                        )}
                    </div>

                    {/* Duration */}
                    <Dropdown
                        label="Duration"
                        value={formValues.duration}
                        onChange={(value) => handleChange({ target: { name: 'duration', value } })}
                        options={durationOptions}
                    />

                    {/* Voice Style */}
                    <Dropdown
                        label="Voice Style"
                        value={formValues.voiceStyle}
                        onChange={(value) => handleChange({ target: { name: 'voiceStyle', value } })}
                        options={voiceStyles}
                    />
                </div>

                {/* Key Points */}
                <label className="flex flex-col gap-2">
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                        Key Points &amp; Context (Optional)
                    </span>
                    <textarea
                        className="resize-none rounded border border-border-dark bg-background-dark p-4 text-slate-100 transition-all focus:border-primary focus:ring-primary"
                        name="keyPoints"
                        onChange={handleChange}
                        placeholder="Describe the core message, tone, and specific data points to include..."
                        rows="3"
                        value={formValues.keyPoints}
                    />
                </label>

                {/* Video Settings */}
                <div className="flex flex-col gap-4 p-4 rounded-lg bg-background-dark/50 border border-border-dark">
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                        Video Settings
                    </span>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <MaterialIcon className="text-slate-400">subtitles</MaterialIcon>
                            <span className="text-sm text-slate-300">Enable Subtitles</span>
                        </div>
                        <ToggleSwitch
                            checked={formValues.enableSubtitles}
                            onChange={(checked) => handleToggle('enableSubtitles', checked)}
                        />
                    </div>
                </div>

                {/* Publish Settings */}
                <div className="flex flex-col gap-4 p-4 rounded-lg bg-background-dark/50 border border-border-dark">
                    <button
                        type="button"
                        onClick={() => setShowPublishSettings(!showPublishSettings)}
                        className="flex items-center justify-between text-left"
                    >
                        <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                            Auto-Publish Settings
                        </span>
                        <MaterialIcon className="text-slate-400">
                            {showPublishSettings ? 'expand_less' : 'expand_more'}
                        </MaterialIcon>
                    </button>

                    {showPublishSettings && (
                        <div className="flex flex-col gap-4 pt-2">
                            <div className="grid grid-cols-2 gap-3">
                                {platforms.map((platform) => (
                                    <button
                                        key={platform.id}
                                        type="button"
                                        onClick={() => handlePlatformToggle(platform.id)}
                                        className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all ${
                                            formValues.publishTo.includes(platform.id)
                                                ? 'border-primary bg-primary/10'
                                                : 'border-border-dark hover:border-slate-600'
                                        }`}
                                    >
                                        <MaterialIcon className="text-xl">{platform.icon}</MaterialIcon>
                                        <span className="text-sm font-medium">{platform.label}</span>
                                    </button>
                                ))}
                            </div>
                            {formValues.publishTo.length > 0 && (
                                <div className="text-xs text-slate-400 flex items-start gap-2">
                                    <MaterialIcon className="text-sm mt-0.5">info</MaterialIcon>
                                    Video will be automatically published to {formValues.publishTo.length} platform(s) with AI-generated captions and hashtags
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="flex justify-end pt-4">
                    <button
                        className="rounded bg-primary px-10 py-4 text-sm font-bold uppercase tracking-widest text-white shadow-prestige transition-all hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-70"
                        disabled={isGenerating}
                        type="submit"
                    >
                        {isGenerating ? 'Generating...' : 'Generate Video'}
                    </button>
                </div>
            </form>
        </section>
    );
}
