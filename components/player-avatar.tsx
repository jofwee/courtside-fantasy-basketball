"use client";

import Image from "next/image";
import { useState } from "react";
import type { Player } from "@/lib/basketball";

function Photo({ src }: { src: string }) {
  const [state, setState] = useState<"loading" | "loaded" | "failed">("loading");
  if (state === "failed") return null;
  return <Image src={src} alt="" fill sizes="40px" loading="lazy" decoding="async"
    referrerPolicy="no-referrer" className={`avatar-photo ${state === "loaded" ? "is-loaded" : ""}`}
    onLoad={() => setState("loaded")} onError={() => setState("failed")} />;
}

export function PlayerAvatar({ player, small = false }: { player: Player; small?: boolean }) {
  const hue = [...player.name].reduce((sum, c) => sum + c.charCodeAt(0), 0) % 65 + 135;
  const id = player.nbaId || (player.id.startsWith("nba:") ? player.id.slice(4) : "");
  const src = /^[1-9]\d{0,11}$/.test(id) ? `https://cdn.nba.com/headshots/nba/latest/260x190/${id}.png` : null;
  return <span className={`avatar ${small ? "small" : ""}`} style={{ background: `hsl(${hue} 24% 91%)`, color: `hsl(${hue} 30% 26%)` }} aria-hidden="true">
    <span className="avatar-initials">{player.name.split(" ").map(n => n[0]).slice(0, 2).join("")}</span>
    {src && <Photo key={src} src={src}/>}
  </span>;
}
