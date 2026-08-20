import React from "react";
import { CheckCircle2, XCircle, Trophy } from "lucide-react";

export interface Tile {
  id: string;
  position: number;
  row: number;
  col: number;
  status: "unanswered" | "correct" | "wrong" | "bingo";
  question_number: number;
  difficulty: string;
}

interface BingoBoardProps {
  size: number;
  tiles: Tile[];
  onTileClick: (tile: Tile) => void;
  disabled?: boolean;
}

export const BingoBoard: React.FC<BingoBoardProps> = ({
  size,
  tiles,
  onTileClick,
  disabled = false,
}) => {
  // Sort tiles to ensure grid order
  const sortedTiles = [...tiles].sort((a, b) => a.position - b.position);

  // Dynamic grid column CSS mapping
  const gridColsClass = {
    3: "grid-cols-3",
    4: "grid-cols-4",
    5: "grid-cols-5",
    6: "grid-cols-6",
  }[size] || "grid-cols-5";

  const getTileStyles = (status: Tile["status"]) => {
    switch (status) {
      case "correct":
        return "bg-emerald-950/70 border-emerald-500 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.15)]";
      case "wrong":
        return "bg-rose-950/70 border-rose-500 text-rose-300 opacity-80 cursor-not-allowed";
      case "bingo":
        return "bg-amber-950/80 border-amber-400 text-amber-200 shadow-[0_0_25px_rgba(245,158,11,0.3)] animate-pulse";
      default:
        return "bg-slate-800/40 border-slate-700 hover:border-blue-400 text-slate-300 hover:text-white hover:bg-slate-800/80 hover:-translate-y-1 hover:shadow-lg hover:shadow-blue-500/5";
    }
  };

  const getDifficultyBadge = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case "hard":
        return "bg-red-950/50 text-red-400 border border-red-800";
      case "medium":
        return "bg-amber-950/50 text-amber-400 border border-amber-800";
      default:
        return "bg-blue-950/50 text-blue-400 border border-blue-800";
    }
  };

  return (
    <div className={`grid ${gridColsClass} gap-3 md:gap-4 w-full aspect-square max-w-2xl mx-auto p-4 rounded-2xl glass-card`}>
      {sortedTiles.map((tile) => {
        const isClickable = tile.status === "unanswered" && !disabled;
        const styles = getTileStyles(tile.status);

        return (
          <button
            key={tile.id}
            onClick={() => isClickable && onTileClick(tile)}
            disabled={!isClickable}
            className={`relative flex flex-col items-center justify-center border rounded-xl p-2 transition-all duration-300 ${styles}`}
          >
            {/* Tile content */}
            <span className="text-xl md:text-2xl font-bold font-mono">
              Q{tile.question_number}
            </span>

            {/* Status Icons */}
            <div className="mt-2">
              {tile.status === "correct" && (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              )}
              {tile.status === "wrong" && (
                <XCircle className="w-5 h-5 text-rose-400" />
              )}
              {tile.status === "bingo" && (
                <Trophy className="w-6 h-6 text-amber-400 animate-bounce" />
              )}
              {tile.status === "unanswered" && (
                <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${getDifficultyBadge(tile.difficulty)}`}>
                  {tile.difficulty}
                </span>
              )}
            </div>

            {/* Tile index (small, in top left) */}
            <span className="absolute top-1 left-2 text-[10px] font-mono text-slate-500">
              {tile.position}
            </span>
          </button>
        );
      })}
    </div>
  );
};
