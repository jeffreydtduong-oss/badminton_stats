from pathlib import Path

from badminton_stats.data import load_game_history


DATA_DIRECTORY = Path(r"E:\Desktop\Badminton apps backup\Stats")


def main() -> None:
    games, files, duplicates_removed = load_game_history(DATA_DIRECTORY)

    print(f"Loaded {len(games):,} games from {len(files)} files")
    print(f"Removed {duplicates_removed:,} exact duplicate rows")
    print("\nSample rows:")
    print(games.head().to_string(index=False))


if __name__ == "__main__":
    main()

print("done")