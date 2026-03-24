import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
      },
    ],
  },
  async rewrites() {
    const internalApiBaseUrl = process.env.API_INTERNAL_BASE_URL;
    if (!internalApiBaseUrl) {
      return [];
    }

    const normalizedBaseUrl = internalApiBaseUrl.startsWith("http")
      ? internalApiBaseUrl
      : `http://${internalApiBaseUrl}`;

    return [
      {
        source: "/api/:path*",
        destination: `${normalizedBaseUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
