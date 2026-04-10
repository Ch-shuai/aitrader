import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'A股智能研究与交易平台',
  description: 'A股智能研究与交易平台 - 支持多策略、多因子、回测调优、AI辅助',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
