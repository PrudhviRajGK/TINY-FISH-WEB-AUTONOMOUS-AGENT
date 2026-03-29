export function MaterialIcon({ children, className = '' }) {
    const classes = ['material-symbols-outlined', className].filter(Boolean).join(' ');

    return (
        <span aria-hidden="true" className={classes}>
            {children}
        </span>
    );
}
