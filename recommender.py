import pandas as pd
import numpy as np
import os
from typing import List, Dict, Any

ALPHA = 0.35
BETA  = 0.25
GAMMA = 0.20
DELTA = 0.20

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "destinations.csv")


def load_destinations() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["vibe_list"]       = df["vibe_all"].apply(
        lambda x: [v.strip().lower() for v in str(x).split(",")])
    df["activities_list"] = df["activities"].apply(
        lambda x: [a.strip() for a in str(x).split(",")])
    return df


def compute_vibe_score(dest_vibes, group_vibes):
    if not group_vibes:
        return 0.5
    matched = sum(group_vibes.get(v, 0) for v in dest_vibes)
    return min(matched / (sum(group_vibes.values()) or 1), 1.0)


def compute_budget_score(dest_cost, group_budget):
    if dest_cost <= group_budget:
        return 1.0 - ((dest_cost / group_budget if group_budget else 1) * 0.3)
    return 0.0


def compute_penalty(dest_cost, group_budget):
    if dest_cost > group_budget:
        return min((dest_cost - group_budget) / group_budget, 1.0)
    return 0.0


def compute_individual_satisfaction(user_vibes, dest_vibes):
    if not user_vibes:
        return 0.5
    return len(set(user_vibes.keys()) & set(dest_vibes)) / (len(user_vibes) or 1)


def compute_group_satisfaction(per_user_vibes, dest_vibes):
    if not per_user_vibes:
        return {"group_satisfaction": 0.6, "fairness_index": 0.0}
    scores = [compute_individual_satisfaction(v, dest_vibes)
              for v in per_user_vibes.values()]
    return {
        "group_satisfaction": float(np.mean(scores)),
        "fairness_index":     float(np.var(scores)) if len(scores) > 1 else 0.0,
    }


def place_ranking_score(row, group_vibes, group_budget):
    cost = float(row["total_estimated_cost_per_person_per_day"])
    return (
        ALPHA * compute_vibe_score(row["vibe_list"], group_vibes)
        + BETA  * compute_budget_score(cost, group_budget)
        + GAMMA * float(row["group_suitability_score"]) / 10.0
        + DELTA * float(row["rating"]) / 5.0
        - 0.3   * compute_penalty(cost, group_budget)
    )


def _state_matches(dest_state: str, preferred_states: List[str]) -> bool:
    """Return True if dest_state matches any of the preferred states."""
    ds = dest_state.lower().strip()
    for ps in preferred_states:
        ps = ps.lower().strip()
        if ps in ds or ds in ps:
            return True
    return False


def build_city_clusters(df, group_vibes, group_budget, per_user_vibes,
                        excluded_vibes, preferred_states):

    df = df.copy()

    # ── 1. State filter (only if user specified states) ────────────────────
    if preferred_states:
        df = df[df["state"].apply(
            lambda s: _state_matches(str(s), preferred_states)
        )]

    # ── 2. Excluded vibe filter ────────────────────────────────────────────
    if excluded_vibes:
        def has_excluded(vibe_list):
            for ev in excluded_vibes:
                ev_l = ev.lower()
                if any(ev_l in dv or dv in ev_l for dv in vibe_list):
                    return True
            return False
        df = df[~df["vibe_list"].apply(has_excluded)]

    if df.empty:
        return []

    # ── 3. Score every remaining place ────────────────────────────────────
    df["place_score"] = df.apply(
        lambda r: place_ranking_score(r, group_vibes, group_budget), axis=1
    )

    group_vibe_set = set(group_vibes.keys())
    city_results   = []

    for city, city_df in df.groupby("city"):
        city_df    = city_df.sort_values("place_score", ascending=False)
        top_places = city_df.head(4)

        covered_vibes = set()
        for _, row in top_places.iterrows():
            covered_vibes.update(row["vibe_list"])

        if group_vibe_set:
            covered_group_vibes = group_vibe_set & covered_vibes
            weighted_coverage   = sum(group_vibes.get(v, 0)
                                      for v in covered_group_vibes)
            coverage_score      = weighted_coverage / (sum(group_vibes.values()) or 1)
        else:
            covered_group_vibes = covered_vibes
            coverage_score = 0.5

        avg_cost         = float(
            top_places["total_estimated_cost_per_person_per_day"].mean())
        best_place_score = float(top_places.iloc[0]["place_score"])

        # Relax coverage threshold when state filter is active
        min_coverage = 0.3 if preferred_states else 0.5
        if coverage_score < min_coverage:
            continue

        city_score = 0.55 * coverage_score + 0.45 * best_place_score

        place_cards = []
        for _, row in top_places.iterrows():
            cost     = float(row["total_estimated_cost_per_person_per_day"])
            sat_data = compute_group_satisfaction(per_user_vibes, row["vibe_list"])
            place_vibes_covered = sorted(
                group_vibe_set & set(row["vibe_list"])) if group_vibe_set else row["vibe_list"][:3]
            place_cards.append({
                "place":                  str(row["place"]),
                "vibe":                   row["vibe_list"],
                "vibes_covered":          place_vibes_covered,
                "cost_per_day":           int(cost),
                "activities":             row["activities_list"][:5],
                "rating":                 float(row["rating"]),
                "why_recommended":        str(row["why_recommended"]),
                "famous_food":            str(row["famous_food"]),
                "best_season":            str(row["best_season"]),
                "ideal_stay":             int(row["ideal_stay_duration_days"]),
                "group_satisfaction_pct": round(sat_data["group_satisfaction"] * 100, 1),
                "budget_fit":             "Within budget" if cost <= group_budget
                                          else f"Over by \u20b9{int(cost - group_budget)}/day",
                "place_score":            round(float(row["place_score"]), 4),
            })

        city_results.append({
            "city":             city,
            "state":            str(top_places.iloc[0]["state"]),
            "city_score":       round(city_score, 4),
            "coverage_pct":     round(coverage_score * 100, 1),
            "avg_cost_per_day": int(avg_cost),
            "best_rating":      float(top_places["rating"].max()),
            "places":           place_cards,
            "covered_vibes":    sorted(covered_group_vibes),
            "missing_vibes":    sorted(group_vibe_set - covered_vibes),
            "excluded_applied": list(excluded_vibes),
            "budget_fit":       "Within budget" if avg_cost <= group_budget
                                else f"Avg over by \u20b9{int(avg_cost - group_budget)}/day",
        })

    city_results.sort(key=lambda x: x["city_score"], reverse=True)
    return city_results[:3]


def rank_destinations(analysis: Dict[str, Any]) -> Dict:
    df              = load_destinations()
    group_vibes     = analysis.get("group_vibes", {})
    group_budget    = analysis.get("budget", 3000)
    per_user_vibes  = analysis.get("per_user_vibes", {})
    excluded_vibes  = analysis.get("excluded_vibes", [])
    # Support both old single string and new list
    raw_states      = analysis.get("preferred_states", analysis.get("preferred_state", ""))
    if isinstance(raw_states, str):
        preferred_states = [raw_states] if raw_states else []
    else:
        preferred_states = [s for s in raw_states if s]

    clusters = build_city_clusters(
        df, group_vibes, group_budget, per_user_vibes,
        excluded_vibes, preferred_states
    )
    return {"city_clusters": clusters}
