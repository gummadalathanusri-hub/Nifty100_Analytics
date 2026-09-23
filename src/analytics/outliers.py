from pathlib import Path

import pandas as pd

from src.analytics.clustering import FEATURES, load_clustering_data

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "output" / "outlier_report.csv"


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Detect sector-level outliers using absolute Z-score greater than 3."""

    records = []

    for sector, group in df.groupby("broad_sector"):
        for feature in FEATURES:
            values = pd.to_numeric(group[feature], errors="coerce")

            mean = values.mean()
            std = values.std(ddof=0)

            if pd.isna(std) or std == 0:
                continue

            z_scores = (values - mean) / std

            for idx, z_score in z_scores.items():
                if pd.notna(z_score) and abs(z_score) > 3:
                    records.append(
                        {
                            "company_id": df.loc[idx, "company_id"],
                            "broad_sector": sector,
                            "field": feature,
                            "value": df.loc[idx, feature],
                            "z_score": z_score,
                            "abs_z_score": abs(z_score),
                            "threshold": 3.0,
                            "issue": "Sector-level outlier",
                            "severity": "HIGH",
                        }
                    )

    return pd.DataFrame(records)


def main():
    """Generate the sector-based outlier report for the Sprint 6 company universe."""
    print("SPRINT 6 - DAY 37 OUTLIER DETECTION")
    print("=" * 50)

    df = load_clustering_data()

    print(f"Companies loaded: {len(df)}")
    print(f"Sectors: {df['broad_sector'].nunique()}")

    outliers = detect_outliers(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    outliers.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutliers detected: {len(outliers)}")
    print(f"Output: {OUTPUT_PATH}")

    if not outliers.empty:
        print("\nOutlier summary:")
        print(
            outliers[
                ["company_id", "broad_sector", "field", "value", "z_score"]
            ].to_string(index=False)
        )

    print("\nCompleted successfully.")


if __name__ == "__main__":
    main()
