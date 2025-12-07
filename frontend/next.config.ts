import type { NextConfig } from "next";

const allowedOrigins = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(",")
  : ["localhost:3000", "127.0.0.1:3000", "0.0.0.0:3000"];

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: allowedOrigins,
    },
  },
  allowedDevOrigins: allowedOrigins,
};

export default nextConfig;
