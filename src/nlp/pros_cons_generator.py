import os
import sqlite3
import numpy as np
import pandas as pd


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DB_FILE = os.path.join(BASE_DIR, "nifty100.db")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "pros_cons_generated.csv"
)

MIN_CONFIDENCE = 60


def confidence_from_strength(strength):

    if pd.isna(strength):
        return None

    strength = float(strength)

    strength = max(
        0,
        min(
            100,
            strength
        )
    )

    return int(
        round(strength)
    )


def add_signal(
    rows,
    company_id,
    signal_type,
    rule_id,
    text,
    confidence,
):

    confidence = confidence_from_strength(
        confidence
    )

    if confidence is None:
        return

    if confidence <= MIN_CONFIDENCE:
        return

    rows.append(
        {
            "company_id": str(company_id),
            "type": signal_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": confidence,
        }
    )


def prepare_year_series(
    df,
    column
):

    if (
        df.empty
        or column not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "year",
                "value"
            ]
        )

    data = df[
        [
            "year",
            column
        ]
    ].copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce"
    )

    data["value"] = pd.to_numeric(
        data[column],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "year",
            "value"
        ]
    )

    data["year"] = data[
        "year"
    ].astype(int)

    data = (
        data[
            [
                "year",
                "value"
            ]
        ]
        .drop_duplicates(
            subset=["year"]
        )
        .sort_values(
            "year"
        )
        .reset_index(
            drop=True
        )
    )

    return data


def years_are_consecutive(
    years
):

    if len(years) < 2:
        return False

    for i in range(
        len(years) - 1
    ):

        if (
            years[i] + 1
            != years[i + 1]
        ):
            return False

    return True


def has_consecutive_sign(
    df,
    column,
    count,
    positive=True
):

    data = prepare_year_series(
        df,
        column
    )

    if len(data) < count:
        return False

    for start in range(
        len(data) - count + 1
    ):

        window = data.iloc[
            start:start + count
        ]

        years = window[
            "year"
        ].tolist()

        if not years_are_consecutive(
            years
        ):
            continue

        values = window[
            "value"
        ]

        if positive:

            if bool(
                (
                    values > 0
                ).all()
            ):
                return True

        else:

            if bool(
                (
                    values < 0
                ).all()
            ):
                return True

    return False


def sustained_above(
    df,
    column,
    threshold,
    years=3
):

    data = prepare_year_series(
        df,
        column
    )

    if len(data) < years:
        return False

    for start in range(
        len(data) - years + 1
    ):

        window = data.iloc[
            start:start + years
        ]

        year_values = window[
            "year"
        ].tolist()

        if not years_are_consecutive(
            year_values
        ):
            continue

        if bool(
            (
                window["value"]
                > threshold
            ).all()
        ):
            return True

    return False


def monotonic_run(
    df,
    column,
    count,
    increasing=True
):

    data = prepare_year_series(
        df,
        column
    )

    if len(data) < count:
        return False

    for start in range(
        len(data) - count + 1
    ):

        window = data.iloc[
            start:start + count
        ]

        years = window[
            "year"
        ].tolist()

        if not years_are_consecutive(
            years
        ):
            continue

        values = window[
            "value"
        ].tolist()

        if increasing:

            if all(
                values[i]
                < values[i + 1]
                for i in range(
                    len(values) - 1
                )
            ):
                return True

        else:

            if all(
                values[i]
                > values[i + 1]
                for i in range(
                    len(values) - 1
                )
            ):
                return True

    return False


def declining_pair(
    df,
    column
):

    data = prepare_year_series(
        df,
        column
    )

    if len(data) < 2:
        return False

    for i in range(
        len(data) - 1
    ):

        previous = data.iloc[i]

        current = data.iloc[
            i + 1
        ]

        if (
            current["year"]
            != previous["year"] + 1
        ):
            continue

        if (
            current["value"]
            < previous["value"]
        ):
            return True

    return False


def has_assets_growing_debt_declining(
    df
):

    required = [
        "year",
        "total_assets",
        "borrowings"
    ]

    if df.empty:
        return False

    if not all(
        column in df.columns
        for column in required
    ):
        return False

    data = df[
        required
    ].copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce"
    )

    data["total_assets"] = pd.to_numeric(
        data["total_assets"],
        errors="coerce"
    )

    data["borrowings"] = pd.to_numeric(
        data["borrowings"],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "year",
            "total_assets",
            "borrowings"
        ]
    )

    data["year"] = data[
        "year"
    ].astype(int)

    data = (
        data
        .drop_duplicates(
            subset=["year"]
        )
        .sort_values(
            "year"
        )
        .reset_index(
            drop=True
        )
    )

    if len(data) < 2:
        return False

    for i in range(
        len(data) - 1
    ):

        previous = data.iloc[i]

        current = data.iloc[
            i + 1
        ]

        if (
            current["year"]
            != previous["year"] + 1
        ):
            continue

        assets_growing = (
            current["total_assets"]
            > previous["total_assets"]
        )

        debt_declining = (
            current["borrowings"]
            < previous["borrowings"]
        )

        if (
            assets_growing
            and debt_declining
        ):
            return True

    return False


def get_latest_value(
    df,
    column
):

    if df.empty:
        return np.nan

    if column not in df.columns:
        return np.nan

    data = df[
        [
            "year",
            column
        ]
    ].copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce"
    )

    data[column] = pd.to_numeric(
        data[column],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "year"
        ]
    )

    if data.empty:
        return np.nan

    data = (
        data
        .sort_values(
            "year"
        )
        .reset_index(
            drop=True
        )
    )

    latest_row = data.iloc[-1]

    return latest_row[column]
   
def load_data():

    con = sqlite3.connect(
        DB_FILE
    )

    companies = pd.read_sql_query(
        """
        SELECT
            id,
            company_name,
            roce_percentage,
            roe_percentage
        FROM companies
        """,
        con
    )

    ratios = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        ORDER BY company_id, year
        """,
        con
    )

    pnl = pd.read_sql_query(
        """
        SELECT *
        FROM profitandloss
        ORDER BY company_id, year
        """,
        con
    )

    cashflow = pd.read_sql_query(
        """
        SELECT *
        FROM cashflow
        ORDER BY company_id, year
        """,
        con
    )

    balancesheet = pd.read_sql_query(
        """
        SELECT *
        FROM balancesheet
        ORDER BY company_id, year
        """,
        con
    )

    market_cap = pd.read_sql_query(
        """
        SELECT *
        FROM market_cap
        ORDER BY company_id, year
        """,
        con
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector
        FROM sectors
        """,
        con
    )

    con.close()

    return (
        companies,
        ratios,
        pnl,
        cashflow,
        balancesheet,
        market_cap,
        sectors
    )


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    print(
        "Loading database..."
    )

    (
        companies,
        ratios,
        pnl,
        cashflow,
        balancesheet,
        market_cap,
        sectors
    ) = load_data()

    target_ids = (
        sectors["company_id"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    ratio_ids = (
        ratios["company_id"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    target_ids = sorted(
        set(target_ids)
        .intersection(
            ratio_ids
        )
    )

    print(
        "Companies table:",
        companies["id"].nunique()
    )

    print(
        "Sector companies:",
        sectors["company_id"].nunique()
    )

    print(
        "Ratio companies:",
        ratios["company_id"].nunique()
    )

    print(
        "Target companies:",
        len(target_ids)
    )

    rows = []

    for company_id in target_ids:

        company_ratios = ratios[
            ratios["company_id"]
            .astype(str)
            == str(company_id)
        ].copy()

        company_pnl = pnl[
            pnl["company_id"]
            .astype(str)
            == str(company_id)
        ].copy()

        company_cf = cashflow[
            cashflow["company_id"]
            .astype(str)
            == str(company_id)
        ].copy()

        company_bs = balancesheet[
            balancesheet["company_id"]
            .astype(str)
            == str(company_id)
        ].copy()

        company_mc = market_cap[
            market_cap["company_id"]
            .astype(str)
            == str(company_id)
        ].copy()

        company_info = companies[
            companies["id"]
            .astype(str)
            == str(company_id)
        ]

        company_sector = sectors[
            sectors["company_id"]
            .astype(str)
            == str(company_id)
        ]

        if company_ratios.empty:
            continue

        company_ratios = (
            company_ratios
            .sort_values(
                "year"
            )
            .reset_index(
                drop=True
            )
        )

        company_pnl = (
            company_pnl
            .sort_values(
                "year"
            )
            .reset_index(
                drop=True
            )
        )

        company_cf = (
            company_cf
            .sort_values(
                "year"
            )
            .reset_index(
                drop=True
            )
        )

        company_bs = (
            company_bs
            .sort_values(
                "year"
            )
            .reset_index(
                drop=True
            )
        )

        company_mc = (
            company_mc
            .sort_values(
                "year"
            )
            .reset_index(
                drop=True
            )
        )

        latest = company_ratios.iloc[
            -1
        ]

        latest_year = latest[
            "year"
        ]

        company_name = str(
            company_id
        )

        if not company_info.empty:

            value = company_info.iloc[
                0
            ].get(
                "company_name"
            )

            if pd.notna(value):
                company_name = str(
                    value
                )

        sector_name = "Unknown"

        if not company_sector.empty:

            value = company_sector.iloc[
                0
            ].get(
                "broad_sector"
            )

            if pd.notna(value):
                sector_name = str(
                    value
                )

        roe_latest = get_latest_value(
            company_ratios,
            "return_on_equity_pct"
        )

        de_latest = get_latest_value(
            company_ratios,
            "debt_to_equity"
        )

        opm_latest = get_latest_value(
            company_ratios,
            "operating_profit_margin_pct"
        )

        fcf_latest = get_latest_value(
            company_ratios,
            "free_cash_flow_cr"
        )

        icr_latest = get_latest_value(
            company_ratios,
            "interest_coverage"
        )

        revenue_cagr = get_latest_value(
            company_ratios,
            "revenue_cagr_5yr"
        )

        pat_cagr = get_latest_value(
            company_ratios,
            "pat_cagr_5yr"
        )

        eps_cagr = get_latest_value(
            company_ratios,
            "eps_cagr_5yr"
        )

        dividend_payout = get_latest_value(
            company_ratios,
            "dividend_payout_ratio_pct"
        )

        net_profit_latest = get_latest_value(
            company_pnl,
            "net_profit"
        )

        sales_latest = get_latest_value(
            company_pnl,
            "sales"
        )

        dividend_yield = np.nan

        if (
            not company_mc.empty
            and
            "dividend_yield_pct"
            in company_mc.columns
        ):

            dividend_yield = get_latest_value(
                company_mc,
                "dividend_yield_pct"
            )

        roce_company = np.nan

        if not company_info.empty:

            roce_company = pd.to_numeric(
                company_info.iloc[
                    0
                ].get(
                    "roce_percentage"
                ),
                errors="coerce"
            )

        fcf_positive_5 = (
            has_consecutive_sign(
                company_ratios,
                "free_cash_flow_cr",
                5,
                positive=True
            )
        )

        fcf_negative_3 = (
            has_consecutive_sign(
                company_ratios,
                "free_cash_flow_cr",
                3,
                positive=False
            )
        )

        roe_sustained = (
            sustained_above(
                company_ratios,
                "return_on_equity_pct",
                20,
                3
            )
        )

        roe_improving = (
            monotonic_run(
                company_ratios,
                "return_on_equity_pct",
                3,
                increasing=True
            )
        )

        de_rising = (
            monotonic_run(
                company_ratios,
                "debt_to_equity",
                3,
                increasing=True
            )
        )

        opm_declining = (
            monotonic_run(
                company_ratios,
                "operating_profit_margin_pct",
                3,
                increasing=False
            )
        )

        eps_declining = (
            monotonic_run(
                company_ratios,
                "earnings_per_share",
                3,
                increasing=False
            )
        )

        revenue_declining = (
            declining_pair(
                company_pnl,
                "sales"
            )
        )

        assets_growing_debt_declining = (
            has_assets_growing_debt_declining(
                company_bs
            )
        )

        de_nonfinancial = (
            sector_name.lower()
            not in {
                "financials",
                "financial services",
                "banks",
                "banking"
            }
        )

        latest_market_cap = np.nan
        latest_ev = np.nan
        latest_ev_ebitda = np.nan

        if not company_mc.empty:

            latest_mc = company_mc.iloc[
                -1
            ]

            latest_market_cap = pd.to_numeric(
                latest_mc.get(
                    "market_cap_crore"
                ),
                errors="coerce"
            )

            latest_ev = pd.to_numeric(
                latest_mc.get(
                    "enterprise_value_crore"
                ),
                errors="coerce"
            )

            latest_ev_ebitda = pd.to_numeric(
                latest_mc.get(
                    "ev_ebitda"
                ),
                errors="coerce"
            )

        net_debt = np.nan
        ebitda = np.nan

        if (
            pd.notna(latest_ev)
            and
            pd.notna(latest_market_cap)
        ):

            net_debt = (
                latest_ev
                - latest_market_cap
            )

        if (
            pd.notna(latest_ev)
            and
            pd.notna(latest_ev_ebitda)
            and
            latest_ev_ebitda > 0
        ):

            ebitda = (
                latest_ev
                / latest_ev_ebitda
            )

        net_debt_gt_3x_ebitda = (
            pd.notna(net_debt)
            and
            pd.notna(ebitda)
            and
            ebitda > 0
            and
            net_debt > 3 * ebitda
        )

        revenue_growth_operating_leverage = (
            pd.notna(revenue_cagr)
            and
            pd.notna(pat_cagr)
            and
            revenue_cagr > pat_cagr
        )

        five_year_revenue_growth = (
            pd.notna(revenue_cagr)
            and
            revenue_cagr > 15
        )

        five_year_pat_growth = (
            pd.notna(pat_cagr)
            and
            pat_cagr > 20
        )

        five_year_eps_growth = (
            pd.notna(eps_cagr)
            and
            eps_cagr > 15
        )

        high_opm = (
            pd.notna(opm_latest)
            and
            opm_latest > 25
        )

        debt_free = (
            pd.notna(de_latest)
            and
            de_latest == 0
        )

        strong_icr = (
            pd.notna(icr_latest)
            and
            icr_latest > 10
        )

        debt_free_or_strong_icr = (
            debt_free
            or
            strong_icr
        )

        dividend_and_fcf = (
            pd.notna(dividend_yield)
            and
            dividend_yield > 2
            and
            pd.notna(fcf_latest)
            and
            fcf_latest > 0
        )

        dividend_payout_over_100 = (
            pd.notna(dividend_payout)
            and
            dividend_payout > 100
        )

        low_icr = (
            pd.notna(icr_latest)
            and
            icr_latest < 1.5
        )

        negative_profit = (
            pd.notna(net_profit_latest)
            and
            net_profit_latest < 0
        )

        low_roce = (
            pd.notna(roce_company)
            and
            roce_company < 10
        )

        high_leverage = (
            de_nonfinancial
            and
            pd.notna(de_latest)
            and
            de_latest > 2
        )

        low_revenue_growth = (
            pd.notna(revenue_cagr)
            and
            revenue_cagr < 5
        )

        if pd.notna(roe_latest):

            roe_strength = min(
                95,
                70
                + max(
                    0,
                    roe_latest - 20
                ) * 0.8
            )

        else:

            roe_strength = np.nan

        if roe_sustained:

            add_signal(
                rows,
                company_id,
                "pro",
                "P01",
                "ROE >20% sustained for 3+ years",
                roe_strength
            )

        if fcf_positive_5:

            add_signal(
                rows,
                company_id,
                "pro",
                "P02",
                "FCF positive for 5+ consecutive years",
                90
            )

        if debt_free:

            add_signal(
                rows,
                company_id,
                "pro",
                "P03",
                "D/E = 0 in the latest year",
                95
            )

        if five_year_revenue_growth:

            strength = min(
                95,
                70
                + (
                    revenue_cagr - 15
                ) * 1.5
            )

            add_signal(
                rows,
                company_id,
                "pro",
                "P04",
                "Revenue CAGR >15% over 5 years",
                strength
            )

        if high_opm:

            strength = min(
                95,
                70
                + (
                    opm_latest - 25
                ) * 1.2
            )

            add_signal(
                rows,
                company_id,
                "pro",
                "P05",
                "OPM >25% in the latest year",
                strength
            )

        if five_year_pat_growth:

            strength = min(
                95,
                70
                + (
                    pat_cagr - 20
                ) * 1.2
            )

            add_signal(
                rows,
                company_id,
                "pro",
                "P06",
                "PAT CAGR >20% over 5 years",
                strength
            )

        if debt_free_or_strong_icr:

            if debt_free:

                confidence = 95

            else:

                confidence = min(
                    95,
                    70
                    + (
                        icr_latest - 10
                    ) * 1.5
                )

            add_signal(
                rows,
                company_id,
                "pro",
                "P07",
                "ICR >10 or Debt Free",
                confidence
            )

        if dividend_and_fcf:

            confidence = min(
                95,
                70
                + (
                    dividend_yield - 2
                ) * 5
                + min(
                    fcf_latest / 10000,
                    10
                )
            )

            add_signal(
                rows,
                company_id,
                "pro",
                "P08",
                "Dividend Yield >2% with positive FCF",
                confidence
            )

        if five_year_eps_growth:

            strength = min(
                95,
                70
                + (
                    eps_cagr - 15
                ) * 1.5
            )

            add_signal(
                rows,
                company_id,
                "pro",
                "P09",
                "EPS CAGR >15% over 5 years",
                strength
            )

        if roe_improving:

            add_signal(
                rows,
                company_id,
                "pro",
                "P10",
                "ROE improving for 3 consecutive years",
                85
            )

        if revenue_growth_operating_leverage:

            add_signal(
                rows,
                company_id,
                "pro",
                "P11",
                "Revenue CAGR exceeds PAT CAGR, indicating operating leverage",
                80
            )

        if assets_growing_debt_declining:

            add_signal(
                rows,
                company_id,
                "pro",
                "P12",
                "Assets growing while borrowings are declining",
                85
            )

        if high_leverage:

            strength = min(
                95,
                70
                + (
                    de_latest - 2
                ) * 5
            )

            add_signal(
                rows,
                company_id,
                "con",
                "C01",
                "D/E >2 for a non-financial company",
                strength
            )

        if fcf_negative_3:

            add_signal(
                rows,
                company_id,
                "con",
                "C02",
                "FCF negative for 3 consecutive years",
                90
            )

        if opm_declining:

            add_signal(
                rows,
                company_id,
                "con",
                "C03",
                "OPM declining for 3 consecutive years",
                85
            )

        if negative_profit:

            add_signal(
                rows,
                company_id,
                "con",
                "C04",
                "Latest net profit is negative",
                95
            )

        if revenue_declining:

            add_signal(
                rows,
                company_id,
                "con",
                "C05",
                "Revenue is declining year over year",
                80
            )

        if low_icr:

            strength = min(
                95,
                75
                + (
                    1.5 - icr_latest
                ) * 10
            )

            add_signal(
                rows,
                company_id,
                "con",
                "C06",
                "ICR <1.5",
                strength
            )

        if dividend_payout_over_100:

            strength = min(
                95,
                75
                + (
                    dividend_payout - 100
                ) * 0.5
            )

            add_signal(
                rows,
                company_id,
                "con",
                "C07",
                "Dividend payout ratio >100%",
                strength
            )

        if de_rising:

            add_signal(
                rows,
                company_id,
                "con",
                "C08",
                "D/E rising for 3 consecutive years",
                85
            )

        if eps_declining:

            add_signal(
                rows,
                company_id,
                "con",
                "C09",
                "EPS declining for 3 consecutive years",
                85
            )

        if low_roce:

            strength = min(
                95,
                75
                + max(
                    0,
                    10 - roce_company
                ) * 2
            )

            add_signal(
                rows,
                company_id,
                "con",
                "C10",
                "ROCE <10%",
                strength
            )

        if net_debt_gt_3x_ebitda:

            leverage_multiple = (
                net_debt / ebitda
            )

            strength = min(
                98,
                75
                + max(
                    0,
                    leverage_multiple - 3
                ) * 5
            )

            add_signal(
                rows,
                company_id,
                "con",
                "C11",
                "Net Debt >3x EBITDA",
                strength
            )

        if low_revenue_growth:

            strength = min(
                95,
                75
                + max(
                    0,
                    5 - revenue_cagr
                ) * 3
            )

            add_signal(
                rows,
                company_id,
                "con",
                "C12",
                "Revenue CAGR <5% over 5 years",
                strength
            )

        financial_sector = (
            sector_name.lower()
            in {
                "financials",
                "financial services",
                "banks",
                "banking",
                "insurance"
            }
        )

        if (
            financial_sector
            and
            pd.isna(icr_latest)
        ):

            add_signal(
                rows,
                company_id,
                "con",
                "C13",
                "Interest coverage ratio is unavailable for this financial company, limiting direct interest-servicing analysis",
                75
            )

    output = pd.DataFrame(
        rows,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct"
        ]
    )

    if output.empty:

        raise RuntimeError(
            "No qualifying pros or cons were generated."
        )

    output["company_id"] = (
        output["company_id"]
        .astype(str)
    )

    output["confidence_pct"] = pd.to_numeric(
        output["confidence_pct"],
        errors="coerce"
    )

    output = output[
        output["confidence_pct"]
        > MIN_CONFIDENCE
    ].copy()

    output = output.drop_duplicates(
        subset=[
            "company_id",
            "type",
            "rule_id"
        ]
    )

    output = output.sort_values(
        [
            "company_id",
            "type",
            "rule_id"
        ]
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        "Pros/Cons generation complete."
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print(
        "Rows:",
        len(output)
    )

    print(
        "Companies:",
        output[
            "company_id"
        ].nunique()
    )

    print()
    print(
        "Type counts:"
    )

    print(
        output[
            "type"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Rule counts:"
    )

    print(
        output[
            "rule_id"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print(
        "Confidence statistics:"
    )

    print(
        output[
            "confidence_pct"
        ]
        .describe()
        .to_string()
    )

    company_counts = (
        output
        .groupby(
            [
                "company_id",
                "type"
            ]
        )
        .size()
        .unstack(
            fill_value=0
        )
    )

    if "pro" not in company_counts.columns:

        company_counts["pro"] = 0

    if "con" not in company_counts.columns:

        company_counts["con"] = 0

    missing_pro = (
        company_counts[
            company_counts["pro"] < 1
        ]
        .index
        .tolist()
    )

    missing_con = (
        company_counts[
            company_counts["con"] < 1
        ]
        .index
        .tolist()
    )

    print()
    print(
        "Companies missing at least 1 pro:",
        len(missing_pro)
    )

    print(
        "Companies missing at least 1 con:",
        len(missing_con)
    )

    if missing_pro:

        print(
            "Missing pro companies:",
            missing_pro
        )

    if missing_con:

        print(
            "Missing con companies:",
            missing_con
        )

    if missing_pro or missing_con:

        raise RuntimeError(
            "Sprint 5 requirement failed: "
            "every target company must have "
            "at least one pro and one con."
        )

    if (
        output["company_id"].nunique()
        != len(target_ids)
    ):

        raise RuntimeError(
            "Output company coverage does not "
            "match the target company count."
        )

    print()
    print(
        "VALIDATION PASSED"
    )

    print(
        "Every target company has at least 1 pro and 1 con."
    )

    print(
        "All included signals have confidence >60%."
    )

    print(
        "Target companies:",
        len(target_ids)
    )


if __name__ == "__main__":
    main()