# Fragment Frontend

This folder contains the React + Vite frontend for the Fragment project.

## Stack

- React
- Vite
- Tailwind CSS
- `@tailwindcss/forms`
- `@tailwindcss/container-queries`
- ESLint

## Environment

Create a `.env` file from `.env.example` when you want to point the frontend at a specific backend:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

If `VITE_API_BASE_URL` is not set, the frontend falls back to the current browser origin.

## Structure

- `src/app/`: app entry composition
- `src/components/ui/`: small shared UI primitives
- `src/features/dashboard/components/`: dashboard sections and page container
- `src/features/dashboard/constants/`: navigation, pipeline, footer, and card data
- `src/features/dashboard/lib/`: feature-specific data shaping
- `src/services/`: backend API configuration and requests
- `src/styles/`: Tailwind entry stylesheet and shared CSS

## Commands

```bash
npm install
npm run dev
npm run build
npm run lint
```
