/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
  // 禁用严格模式以防止双重渲染问题
  reactStrictMode: false,
};

module.exports = nextConfig;
