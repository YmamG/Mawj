import type { NextConfig } from "next";
const backend = process.env.DJANGO_URL || "http://127.0.0.1:8000";
const config: NextConfig = {
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*/` }];
  },
};
export default config;
