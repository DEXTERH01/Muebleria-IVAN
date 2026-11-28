type BrandMarkProps = { animated?: boolean; inverse?: boolean };

const cabinetFrame = 'M24 222V26L140 101L256 26V222H208V123L140 166L72 123V222H24Z';
const leftDoor = 'M78 130L134 166V216H78Z';
const rightDoor = 'M146 166L202 130V216H146Z';

export function BrandMark({ animated = false, inverse = false }: BrandMarkProps) {
  const classes = ['brand-mark', inverse && 'is-inverse', animated && 'is-animated']
    .filter(Boolean)
    .join(' ');

  return (
    <svg
      className={classes}
      viewBox="0 0 280 240"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <path className="brand-mark-frame" d={cabinetFrame} />
      <path className="brand-mark-door brand-mark-door-left" d={leftDoor} />
      <path className="brand-mark-door brand-mark-door-right" d={rightDoor} />
      <path className="brand-mark-handle" d="M124 174h6v22h-6zm26 0h6v22h-6z" />
    </svg>
  );
}
