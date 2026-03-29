import { MaterialIcon } from '../../../components/ui/MaterialIcon.jsx';

function getBarClasses(step) {
    if (step.status === 'complete') {
        return 'h-1 w-full rounded-full bg-primary';
    }

    if (step.status === 'active') {
        return 'relative h-1 w-full overflow-hidden rounded-full bg-primary/20';
    }

    if (step.status === 'error') {
        return 'h-1 w-full rounded-full bg-red-700/70';
    }

    return 'h-1 w-full rounded-full bg-border-dark';
}

function getIconClasses(step) {
    if (step.status === 'pending') {
        return 'text-xl text-slate-600';
    }

    if (step.status === 'error') {
        return 'text-xl text-red-500';
    }

    return 'text-xl text-primary';
}

function getLabelClasses(step) {
    if (step.status === 'error') {
        return 'text-xs font-bold text-red-400';
    }

    return step.status === 'pending'
        ? 'text-xs font-bold text-slate-500'
        : 'text-xs font-bold text-slate-100';
}

export function PipelineSection({ statusText, steps }) {
    return (
        <section className="scroll-mt-32 flex flex-col gap-6" id="pipeline-section">
            <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-[0.3em] text-slate-500">
                    Automation Pipeline
                </h3>
                <span className="text-[10px] font-bold uppercase tracking-widest text-primary">
                    {statusText}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
                {steps.map((step) => (
                    <div className="group flex flex-col gap-3" key={step.label}>
                        <div className={getBarClasses(step)}>
                            {step.status === 'active' ? (
                                <div className="absolute inset-y-0 left-0 w-2/3 bg-primary" />
                            ) : null}
                        </div>
                        <div className="flex items-center gap-3">
                            <MaterialIcon className={getIconClasses(step)}>{step.icon}</MaterialIcon>
                            <span className={getLabelClasses(step)}>{step.label}</span>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
