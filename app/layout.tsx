import type { Metadata } from "next";
import "@fontsource-variable/dm-sans";
import "@fontsource-variable/manrope";
import "./globals.css";
export const metadata: Metadata = { title: "Courtside — Fantasy basketball trade analyzer", description: "See the whole picture. Compare NBA trades and understand their impact on your eight-category fantasy roster." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
