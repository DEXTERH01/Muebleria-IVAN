export function BrandMark({ animated = false }: { animated?: boolean }) {
  return (
    <svg
      className={animated ? 'brand-mark is-animated' : 'brand-mark'}
      viewBox="0 0 72 72"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <path className="brand-mark-line" d="M13 23 36 11l23 12" />
      <path className="brand-mark-line" d="M12 25h48v5H12z" />
      <path className="brand-mark-line" d="M16 30v27a3 3 0 0 0 3 3h34a3 3 0 0 0 3-3V30" />
      <path className="brand-mark-line" d="M22 35h11v19H22zM39 35h11v19H39z" />
      <path className="brand-mark-line" d="M36 31v29M22 43v-4l5.5 5 5.5-5v4" />
      <path className="brand-mark-line" d="M22 60v4m28-4v4" />
      <circle className="brand-mark-line" cx="29" cy="46" r="1.2" />
      <circle className="brand-mark-line" cx="43" cy="46" r="1.2" />
    </svg>
  );
}
