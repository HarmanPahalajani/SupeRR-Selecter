import PlayerProfileClient from "./PlayerProfileClient";
import playerIndex from "@/public/data/players/index.json";

export async function generateStaticParams() {
  try {
    return (playerIndex.items || []).map((p: any) => ({
      playerId: String(p.player_id),
    }));
  } catch (err) {
    console.error("Error in generateStaticParams:", err);
    return [{ playerId: "47" }, { playerId: "4847" }, { playerId: "2933" }, { playerId: "3535" }];
  }
}

export default function Page({ params }: { params: { playerId: string } }) {
  return <PlayerProfileClient initialPlayerId={Number(params.playerId)} />;
}
