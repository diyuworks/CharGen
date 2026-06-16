interface Props {
  size?: number;
  text?: string;
}

export default function LoadingSpinner({ size = 24, text }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        style={{ width: size, height: size }}
        className="border-2 border-white/10 border-t-violet-500 rounded-full animate-spin"
      />
      {text && <p className="text-white/40 text-sm">{text}</p>}
    </div>
  );
}
