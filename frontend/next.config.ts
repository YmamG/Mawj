import type { NextConfig } from "next";
import { networkInterfaces } from "node:os";
const backend = process.env.DJANGO_URL || "http://127.0.0.1:8000";
const localAddresses = Object.values(networkInterfaces()).flatMap((rows) =>
  (rows || []).filter((row) => row.family === "IPv4" && !row.internal).map((row) => row.address),
);
const config: NextConfig = {
  skipTrailingSlashRedirect: true,
  allowedDevOrigins: ["localhost", "127.0.0.1", ...localAddresses],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*/` }];
  },
};
export default config;
