import type { NextConfig } from "next";
const config: NextConfig = { poweredByHeader: false, devIndicators: false, images: { remotePatterns: [{ protocol: "https", hostname: "cdn.nba.com", pathname: "/headshots/nba/latest/260x190/**", search: "" }] } };
export default config;
