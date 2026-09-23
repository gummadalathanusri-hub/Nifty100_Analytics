"""
Sprint 6 - Day 36
KMeans company clustering for the 92-company Sprint 6 universe.
"""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "nifty100.db"
UNIVERSE_PATH = ROOT_DIR / "output" / "sprint6_company_universe.csv"
CASHFLOW_PATH = ROOT_DIR / "output" / "cashflow_intelligence.xlsx"
OUTPUT_DIR = ROOT_DIR / "output"
REPORTS_DIR = ROOT_DIR / "reports"

CLUSTER_LABELS_PATH = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_PATH = REPORTS_DIR / "elbow_plot.png"

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

N_CLUSTERS = 5
RANDOM_STATE = 42


def load_clustering_data() -> pd.DataFrame:
    """Load the 92-company clustering dataset."""
    universe = pd.read_csv(UNIVERSE_PATH)

    if "id" not in universe.columns:
        raise ValueError("Universe file must contain an 'id' column.")

    company_ids = universe["id"].dropna().astype(str).unique().tolist()

    if len(company_ids) != 92:
        raise ValueError(
            f"Expected 92 companies in Sprint 6 universe, found {len(company_ids)}."
        )

    placeholders = ",".join(["?"] * len(company_ids))

    query = f"""
        SELECT
            f.company_id,
            f.year,
            f.return_on_equity_pct,
            f.debt_to_equity,
            f.revenue_cagr_5yr,
            f.operating_profit_margin_pct,
            s.broad_sector
        FROM financial_ratios f
        JOIN sectors s
            ON f.company_id = s.company_id
        WHERE f.year = (
            SELECT MAX(year)
            FROM financial_ratios
        )
        AND f.company_id IN ({placeholders})
    """

    with sqlite3.connect(DB_PATH) as conn:
        ratios = pd.read_sql_query(query, conn, params=company_ids)

    cashflow = pd.read_excel(
        CASHFLOW_PATH,
        usecols=["company_id", "fcf_cagr_5yr"],
    )

    df = ratios.merge(
        cashflow,
        on="company_id",
        how="left",
        validate="one_to_one",
    )

    if len(df) != 92:
        raise ValueError(f"Expected 92 clustering rows after merge, found {len(df)}.")

    return df


def impute_sector_medians(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing clustering features using sector medians."""
    result = df.copy()

    for feature in FEATURES:
        sector_medians = result.groupby("broad_sector")[feature].transform("median")

        result[feature] = result[feature].fillna(sector_medians)
        if result[feature].isna().any():
            overall_median = result[feature].median()

            if pd.isna(overall_median):
                raise ValueError(f"Cannot impute {feature}: no valid values available.")

            result[feature] = result[feature].fillna(overall_median)

    return result


def create_elbow_plot(X: pd.DataFrame) -> None:
    """Create and save the KMeans elbow plot for k=2 through k=10."""
    inertias = []
    k_values = range(2, 11)

    for k in k_values:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=10,
        )
        model.fit(X)
        inertias.append(model.inertia_)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 6))
    plt.plot(list(k_values), inertias, marker="o")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")
    plt.xticks(list(k_values))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(ELBOW_PATH, dpi=150)
    plt.close()


def run_kmeans(df: pd.DataFrame) -> pd.DataFrame:
    """Scale features and assign each company to one of five clusters."""
    scaler = StandardScaler()
    X = scaler.fit_transform(df[FEATURES])

    create_elbow_plot(pd.DataFrame(X, columns=FEATURES))

    model = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=10,
    )

    cluster_ids = model.fit_predict(X)

    distances = model.transform(X)
    distance_from_centroid = distances[
        range(len(X)),
        cluster_ids,
    ]

    result = df[["company_id"]].copy()
    result["cluster_id"] = cluster_ids
    result["cluster_name"] = result["cluster_id"].map(
        {
            0: "High-Margin Compounders",
            1: "Core Quality Companies",
            2: "Leveraged Growth",
            3: "High-ROE Outliers",
            4: "Cash-Flow Accelerators",
        }
    )
    result["distance_from_centroid"] = distance_from_centroid

    return result


def main() -> None:
    """Run the Sprint 6 Day 36 clustering pipeline."""
    print("SPRINT 6 - DAY 36 KMEANS CLUSTERING")
    print("=" * 50)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_clustering_data()

    print(f"Companies loaded: {len(df)}")
    print(f"Latest year: {df['year'].unique().tolist()}")

    print("\nMissing values before imputation:")
    print(df[FEATURES].isna().sum().to_string())

    df = impute_sector_medians(df)

    print("\nMissing values after sector-median imputation:")
    print(df[FEATURES].isna().sum().to_string())

    result = run_kmeans(df)

    result = result.sort_values("company_id").reset_index(drop=True)

    result.to_csv(
        CLUSTER_LABELS_PATH,
        index=False,
    )

    print("\nCluster counts:")
    print(result["cluster_id"].value_counts().sort_index().to_string())

    print("\nOutput:")
    print(CLUSTER_LABELS_PATH)

    print("\nElbow plot:")
    print(ELBOW_PATH)

    print("\nCompleted successfully.")


if __name__ == "__main__":
    main()
