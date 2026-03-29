import { pipelineSteps } from '../constants/pipelineSteps.js';

/**
 * Build pipeline step states based on current mode and active step
 * @param {string} mode - Pipeline mode: 'idle', 'running', 'complete', 'error'
 * @param {string|null} activeStepKey - Currently active step key
 * @returns {Array} Array of step objects with status
 */
export function buildPipelineStepStates(mode, activeStepKey) {
    if (mode === 'idle') {
        return pipelineSteps.map((step) => ({
            ...step,
            status: 'pending',
        }));
    }

    if (mode === 'complete') {
        return pipelineSteps.map((step) => ({
            ...step,
            status: 'complete',
        }));
    }

    if (mode === 'error') {
        return pipelineSteps.map((step) => {
            if (step.key === activeStepKey) {
                return { ...step, status: 'error' };
            }
            const activeIndex = pipelineSteps.findIndex((s) => s.key === activeStepKey);
            const stepIndex = pipelineSteps.findIndex((s) => s.key === step.key);
            return {
                ...step,
                status: stepIndex < activeIndex ? 'complete' : 'pending',
            };
        });
    }

    // mode === 'running'
    return pipelineSteps.map((step) => {
        if (step.key === activeStepKey) {
            return { ...step, status: 'active' };
        }
        const activeIndex = pipelineSteps.findIndex((s) => s.key === activeStepKey);
        const stepIndex = pipelineSteps.findIndex((s) => s.key === step.key);
        return {
            ...step,
            status: stepIndex < activeIndex ? 'complete' : 'pending',
        };
    });
}
