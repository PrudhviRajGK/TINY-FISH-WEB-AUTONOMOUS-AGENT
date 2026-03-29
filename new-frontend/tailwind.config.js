import forms from '@tailwindcss/forms';
import containerQueries from '@tailwindcss/container-queries';

/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: ['./index.html', './src/**/*.{js,jsx}'],
    theme: {
        extend: {
            colors: {
                primary: '#8B0000',
                'background-light': '#f8f8f5',
                'background-dark': '#0a0a0a',
                'surface-dark': '#1a1a1a',
                'border-dark': '#2a2a2a',
            },
            fontFamily: {
                display: ['Space Grotesk', 'sans-serif'],
            },
            borderRadius: {
                DEFAULT: '0.125rem',
                lg: '0.25rem',
                xl: '0.5rem',
                full: '0.75rem',
            },
            boxShadow: {
                prestige: '0 0 20px rgba(139, 0, 0, 0.3)',
            },
        },
    },
    plugins: [forms, containerQueries],
};
