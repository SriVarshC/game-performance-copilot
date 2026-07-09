// ═══════════════════════════════════════════════════════════
// Icon set — thin-stroke SVGs replacing emoji throughout the app
// ═══════════════════════════════════════════════════════════

interface IconProps {
  size?: number;
  color?: string;
}

const base = { fill: "none", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export const IconDashboard = ({ size = 18, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" />
    <rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" />
  </svg>
);

export const IconAnalytics = ({ size = 18, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16" y2="16" />
    <path d="M8 11h6M11 8v6" />
  </svg>
);

export const IconTarget = ({ size = 18, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" />
  </svg>
);

export const IconCopilot = ({ size = 18, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <rect x="4" y="7" width="16" height="12" rx="1" />
    <path d="M9 3v4M15 3v4M8 13h.01M16 13h.01M9 17h6" />
  </svg>
);

export const IconBolt = ({ size = 18, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" />
  </svg>
);

export const IconCpu = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <rect x="6" y="6" width="12" height="12" rx="1" />
    <path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3" />
  </svg>
);

export const IconGpu = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <rect x="2" y="7" width="20" height="10" rx="1" />
    <circle cx="7" cy="12" r="2" /><path d="M13 12h6M2 17v2M20 17v2" />
  </svg>
);

export const IconRam = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <rect x="3" y="9" width="18" height="7" rx="1" />
    <path d="M7 9V6M11 9V6M15 9V6M7 16v3M11 16v3M15 16v3" />
  </svg>
);

export const IconThermometer = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M12 3a2 2 0 0 1 2 2v9.5a4 4 0 1 1-4 0V5a2 2 0 0 1 2-2z" />
  </svg>
);

export const IconRadio = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <circle cx="12" cy="12" r="2" />
    <path d="M8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7M5.5 5.5a9 9 0 0 0 0 13M18.5 5.5a9 9 0 0 1 0 13" />
  </svg>
);

export const IconThumbsUp = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M7 11v9H4v-9h3zm0 0 4-8a2 2 0 0 1 2 2v4h5a2 2 0 0 1 2 2l-1.5 7a2 2 0 0 1-2 1.5H9" />
  </svg>
);

export const IconThumbsDown = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M17 13V4h3v9h-3zm0 0-4 8a2 2 0 0 1-2-2v-4H6a2 2 0 0 1-2-2l1.5-7A2 2 0 0 1 7.5 4.5H15" />
  </svg>
);

export const IconRefresh = ({ size = 14, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M21 12a9 9 0 1 1-3-6.7" /><path d="M21 4v5h-5" />
  </svg>
);

export const IconUser = ({ size = 14, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <circle cx="12" cy="8" r="4" /><path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
  </svg>
);

export const IconAlert = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M12 3 2 20h20L12 3z" /><path d="M12 10v4M12 17h.01" />
  </svg>
);

export const IconLink = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M9 15 15 9" /><path d="M11 6l1-1a4 4 0 0 1 6 6l-1 1" /><path d="M13 18l-1 1a4 4 0 0 1-6-6l1-1" />
  </svg>
);

export const IconTrend = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M3 17l6-6 4 4 8-8" /><path d="M15 7h6v6" />
  </svg>
);

export const IconGamepad = ({ size = 16, color = "currentColor" }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" stroke={color} {...base}>
    <path d="M6 8h4M8 6v4M15 9h.01M18 11h.01" />
    <path d="M7 6h10a4 4 0 0 1 4 4l1 5a3 3 0 0 1-5.5 1.8L15 15H9l-1.5 1.8A3 3 0 0 1 2 15l1-5a4 4 0 0 1 4-4z" />
  </svg>
);