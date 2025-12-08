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
  async rewrites() {
    return [
      {
        source: '/auth/:path*',
        destination: 'http://backend:8000/auth/:path*',
      },
      {
        source: '/turnos/:path*',
        destination: 'http://backend:8000/turnos/:path*',
      },
      {
        source: '/usuarios/:path*',
        destination: 'http://backend:8000/usuarios/:path*',
      },
      {
        source: '/relatorios/:path*',
        destination: 'http://backend:8000/relatorios/:path*',
      },
      {
        source: '/assinaturas/:path*',
        destination: 'http://backend:8000/assinaturas/:path*',
      },
    ];
  },
};

export default nextConfig;