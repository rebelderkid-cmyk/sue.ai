import type { NextConfig } from "next";

// Vercel Deployment Config
const nextConfig: NextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
  },
  /* config options here */
};

export default nextConfig;
