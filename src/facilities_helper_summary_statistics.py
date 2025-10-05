import pandas as pd

def extract_facility_summary(df, facility_type, targets):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # --- Filter by type if not "Total"
    if facility_type.lower() != "total":
        df = df[df["type"].str.lower() == facility_type.lower()]

    # --- Group by date and status
    grouped = (
        df.groupby(["date", "status"])["n_facilities"]
        .sum()
        .unstack(fill_value=0)
        .sort_index()
    )

    # --- Extract trends ---
    energized_trend = grouped.get("Energized", pd.Series([0]*len(grouped)))
    # Anything not 'Energized' counts as 'not energized'
    not_energized_trend = grouped.drop(columns=["Energized"], errors="ignore").sum(axis=1)
    dates = grouped.index.tolist()

    # --- Compute latest snapshot ---
    target = targets.get(facility_type, targets.get("Total", 0))
    energized = int(energized_trend.iloc[-1]) if len(energized_trend) else 0
    not_energized = int(not_energized_trend.iloc[-1]) if len(not_energized_trend) else 0
    planned = energized + not_energized
    percent = energized / target if target > 0 else 0

    # --- Compute increase from previous date ---
    if len(energized_trend) > 1:
        increase = energized_trend.iloc[-1] - energized_trend.iloc[-2]
    else:
        increase = 0

    return {
        "type": facility_type.title(),
        "target": int(target),
        "energized": energized,
        "in_progress": not_energized,
        "planned": planned,
        "percent": round(percent, 3),
        "increase": int(increase),
        "energized_trend": energized_trend.tolist(),
        "dates": [d.strftime("%Y-%m-%d") for d in dates],
    }
