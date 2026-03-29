import { useEffect } from 'react';
import { MaterialIcon } from './MaterialIcon.jsx';

export function NotificationToast({ message, type = 'info', onClose, duration = 5000 }) {
    useEffect(() => {
        if (duration > 0) {
            const timer = setTimeout(onClose, duration);
            return () => clearTimeout(timer);
        }
    }, [duration, onClose]);

    const icons = {
        success: 'check_circle',
        error: 'error',
        warning: 'warning',
        info: 'info',
    };

    const colors = {
        success: 'bg-green-600',
        error: 'bg-red-600',
        warning: 'bg-yellow-600',
        info: 'bg-blue-600',
    };

    return (
        <div
            className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-lg ${colors[type]} px-6 py-4 text-white shadow-lg animate-slide-in`}
        >
            <MaterialIcon className="text-2xl">{icons[type]}</MaterialIcon>
            <span className="text-sm font-medium">{message}</span>
            <button
                onClick={onClose}
                className="ml-4 hover:opacity-75 transition-opacity"
            >
                <MaterialIcon className="text-xl">close</MaterialIcon>
            </button>
        </div>
    );
}
