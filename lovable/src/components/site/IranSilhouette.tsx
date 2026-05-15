export function IranSilhouette({ className = "" }: { className?: string }) {
  // Stylized abstract Iran silhouette (decorative, non-interactive)
  return (
    <svg
      viewBox="0 0 200 180"
      className={className}
      aria-hidden="true"
      fill="currentColor"
    >
      <path d="M40,40 C55,28 80,24 100,28 C125,32 150,28 170,40 C182,48 188,68 180,90 C176,108 184,124 170,140 C152,158 124,160 100,156 C76,160 52,156 36,142 C22,128 24,108 28,92 C18,72 24,52 40,40 Z" />
    </svg>
  );
}
