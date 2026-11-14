/** @type {import('next').NextConfig} */
const isStaticExport = process.env.NEXT_EXPORT === 'true' || process.env.NODE_ENV === 'production';

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['react-plotly.js', 'plotly.js-dist-min'],
  ...(isStaticExport
    ? {
        output: 'export',
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {
        async rewrites() {
          return [
            {
              source: '/api/:path*',
              destination: 'http://127.0.0.1:8000/api/:path*',
            },
          ];
        },
      }),
};

module.exports = nextConfig;
