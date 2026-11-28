export function BrandMark({ animated = false, inverse = false }: { animated?: boolean; inverse?: boolean }) {
  return (
    <img
      className={animated ? 'brand-mark is-animated' : 'brand-mark'}
      src={inverse ? '/assets/brand/muebleria-ivan-monogram-inverse.svg' : '/assets/brand/muebleria-ivan-logo.svg'}
      alt=""
      aria-hidden="true"
      draggable="false"
    />
  );
}
