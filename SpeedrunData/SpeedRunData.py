import srcomapi
import srcomapi.datatypes as dt
import pandas as pd

api = srcomapi.SpeedrunCom()
api.debug = 1

search_results = api.search(dt.Game, {"name": "super mario 64"})
if not search_results:
    print("Game not found")
    exit()

game = search_results[0]
print("Game found:", game.name)

print("Categories:")
for cat in game.categories:
    print("-", cat.name)

MAX_RUNS = 6000

sms_runs = {}
for category in game.categories:
    if category.type == 'per-level':
        continue  # Skip per-level categories

    if category.name not in sms_runs:
        sms_runs[category.name] = {}

    leaderboard = dt.Leaderboard(
        api,
        data=api.get(f"leaderboards/{game.id}/category/{category.id}?embed=variables")
    )
    sms_runs[category.name] = leaderboard

    data_rows = []
    for entry in leaderboard.runs:
        if len(data_rows) >= MAX_RUNS:
            print(f"Reached {MAX_RUNS} runs for category '{category.name}', stopping.")
            break

        place = entry['place'] if isinstance(entry, dict) and 'place' in entry else entry.place
        run = entry['run'] if isinstance(entry, dict) and 'run' in entry else entry.run
        players = getattr(run, 'players', None) or (run['players'] if isinstance(run, dict) and 'players' in run else [])
        if not players:
            continue

        player_info = players[0]
        role = getattr(player_info, 'role', getattr(player_info, 'rel', None))
        if role == 'guest' or not hasattr(player_info, 'id'):
            print(f"Skipping guest run for player: {getattr(player_info, 'name', 'Unknown')}")
            continue

        player_name = getattr(player_info, 'name', 'Unknown')
        time_sec = getattr(run, 'times', {}).get('primary_t', None) if hasattr(run, 'times') else run['times']['primary_t']
        submitted = getattr(run, 'submitted', '') if hasattr(run, 'submitted') else run.get('submitted', '')
        data_rows.append({'Place': place, 'Player': player_name, 'Time (seconds)': time_sec, 'Date Submitted': submitted})

    df = pd.DataFrame(data_rows)
    filename = f"{game.name.replace(' ', '_')}_{category.name.replace(' ', '_')}_leaderboard.csv"
    df.to_csv(filename, index=False)
    print(f"Saved {filename} with {len(data_rows)} runs")
