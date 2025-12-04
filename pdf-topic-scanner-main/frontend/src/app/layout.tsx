import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DocTree.AI',
  description: 'Extract and visualize PDF document hierarchies with AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
