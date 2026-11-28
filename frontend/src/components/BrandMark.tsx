export function BrandMark({ animated = false }: { animated?: boolean }) {
  return (
    <img
      className={animated ? 'brand-mark is-animated' : 'brand-mark'}
      src="/assets/brand/muebleria-ivan-logo.svg"
      alt=""
      aria-hidden="true"
      draggable="false"
    />
  );
}
