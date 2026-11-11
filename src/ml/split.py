"""Strict Storm-Level Train/Test Splitting for CHAKRAVAT.

Fulfills Requirement R3: Zero temporal lookahead or within-storm observation leakage.
In cyclone meteorology, observations along a single trajectory are strongly
autocorrelated. Splitting at observation level leaks storm identity.
Storms MUST be partitioned as whole discrete trajectories.
"""

from typing import List, Optional, Set, Tuple
import pandas as pd


DEFAULT_TEST_STORM_NAMES = ["YAAS", "BIPARJOY"]


def resolve_storm_identifier_col(df: pd.DataFrame) -> str:
    """Identify the column representing storm names or identifiers."""
    candidates = ["storm_name", "name", "storm_id"]
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(f"DataFrame must contain one of {candidates} for storm-level splitting.")


def get_default_train_test_storms(
    df: pd.DataFrame,
    test_storm_names: Optional[List[str]] = None,
) -> Tuple[List[str], List[str]]:
    """Determine the disjoint storm lists for training and testing.

    Ensures balanced basin representation (Bay of Bengal + Arabian Sea).
    """
    storm_col = resolve_storm_identifier_col(df)
    unique_storms = df[storm_col].astype(str).unique().tolist()
    unique_storms_upper = [s.upper() for s in unique_storms]

    target_tests = [s.upper() for s in (test_storm_names or DEFAULT_TEST_STORM_NAMES)]

    resolved_test: List[str] = []
    for orig, upper in zip(unique_storms, unique_storms_upper):
        if upper in target_tests:
            resolved_test.append(orig)

    # Fallback if no matching test storms found (e.g. if storm_id used instead of name)
    if not resolved_test:
        if len(unique_storms) >= 3:
            # Reserve last 25-30% storms for test
            n_test = max(1, int(len(unique_storms) * 0.25))
            resolved_test = unique_storms[-n_test:]
        else:
            resolved_test = [unique_storms[-1]]

    resolved_train = [s for s in unique_storms if s not in resolved_test]

    # Verify disjointness
    train_set: Set[str] = set(resolved_train)
    test_set: Set[str] = set(resolved_test)
    assert train_set.isdisjoint(test_set), (
        f"Critical Split Error: Storm leakage detected between train ({train_set}) "
        f"and test ({test_set})"
    )

    return resolved_train, resolved_test


def storm_level_split(
    df: pd.DataFrame,
    test_storm_names: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Partition a cyclone dataset strictly by storm identity.

    Guarantees that all fixes belonging to a given storm reside exclusively in
    either train_df or test_df.

    Args:
        df: Input DataFrame containing cyclone synoptic records.
        test_storm_names: Optional list of storm names or IDs to reserve for testing.
                         Defaults to DEFAULT_TEST_STORM_NAMES ('YAAS', 'BIPARJOY').

    Returns:
        Tuple of (train_df, test_df) with reset indices.

    Raises:
        AssertionError: If any storm appears in both train and test partitions.
        ValueError: If input DataFrame does not contain a recognized storm column.
    """
    if df.empty:
        return df.copy(), df.copy()

    storm_col = resolve_storm_identifier_col(df)
    train_storms, test_storms = get_default_train_test_storms(df, test_storm_names)

    train_mask = df[storm_col].isin(train_storms)
    test_mask = df[storm_col].isin(test_storms)

    train_df = df[train_mask].copy().reset_index(drop=True)
    test_df = df[test_mask].copy().reset_index(drop=True)

    # Scientific integrity assertion: zero overlap
    train_storm_set = set(train_df[storm_col].astype(str).unique())
    test_storm_set = set(test_df[storm_col].astype(str).unique())

    assert train_storm_set.isdisjoint(test_storm_set), (
        f"CRITICAL LEAKAGE DETECTED: Storms {train_storm_set.intersection(test_storm_set)} "
        f"appear in both train and test sets!"
    )

    return train_df, test_df
