import { loadDataset } from "@/lib/data";
import { Analyzer } from "@/components/analyzer";
import { RefreshCw } from "lucide-react";
export const dynamic = "force-dynamic";
export default async function Page() {
  try { return <Analyzer data={await loadDataset()} />; }
  catch { return <main className="connection-error"><span className="brand">courtside<span>↗</span></span><div><RefreshCw size={32} /><h1>Your trade desk is taking a timeout.</h1><p>We couldn’t load the player data. Check your connection and try again. Your saved roster stays in this browser.</p><a className="primary-button" href="/">Try again</a></div></main>; }
}
