import sys
import io
import warnings

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "Menstural_cyclelength.csv"
MODEL_DIR = Path(__file__).resolve().parent / "model"
MODEL_DIR.mkdir(exist_ok=True)


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["cycle_length"] = pd.to_numeric(df["cycle_length"], errors="coerce")
    df["cycle_length"] = df["cycle_length"].clip(15, 60)
    df = df.sort_values(["new_id", "cycle_number"]).reset_index(drop=True)
    return df


def build_pairs(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for uid, grp in df.groupby("new_id"):
        grp = grp.reset_index(drop=True)
        for i in range(len(grp) - 1):
            curr = grp.iloc[i]
            nxt = grp.iloc[i + 1]
            if nxt["cycle_number"] - curr["cycle_number"] != 1:
                continue
            if pd.isna(curr["cycle_length"]) or pd.isna(nxt["cycle_length"]):
                continue
            records.append({
                "user_id": uid,
                "age": curr["age"],
                "cycle_number": curr["cycle_number"],
                "cycle_length": curr["cycle_length"],
                "next_cycle_length": nxt["cycle_length"],
            })
    return pd.DataFrame(records)


def engineer_features(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for uid, grp in pairs.groupby("user_id"):
        grp = grp.sort_values("cycle_number").reset_index(drop=True)
        history: list[float] = []

        for _, row in grp.iterrows():
            cl = row["cycle_length"]
            n = len(history)

            lag1 = history[-1] if n >= 1 else cl
            lag2 = history[-2] if n >= 2 else lag1
            lag3 = history[-3] if n >= 3 else lag2

            prev = history if history else [cl]
            mean_all = float(np.mean(prev))
            std_all = float(np.std(prev)) if len(prev) > 1 else 0.0
            mean3 = float(np.mean(prev[-3:])) if len(prev) >= 3 else float(np.mean(prev))
            mean6 = float(np.mean(prev[-6:])) if len(prev) >= 6 else float(np.mean(prev))

            # Coefficient of variation (relative variability of personal cycle)
            cv = std_all / mean_all if mean_all > 0 else 0.0

            rows.append({
                "user_id": uid,
                "age": row["age"],
                "cycle_number": row["cycle_number"],
                "cycle_length": cl,
                "lag1": lag1,
                "lag2": lag2,
                "lag3": lag3,
                "mean_all": mean_all,
                "std_all": std_all,
                "mean3": mean3,
                "mean6": mean6,
                "trend": lag1 - lag2,
                "dev_from_mean": cl - mean_all,
                "cv_personal": cv,
                "n_recorded": n,
                "next_cycle_length": row["next_cycle_length"],
            })
            history.append(cl)

    return pd.DataFrame(rows).dropna()


FEATURE_COLS = [
    "age", "cycle_number", "cycle_length",
    "lag1", "lag2", "lag3",
    "mean_all", "std_all", "mean3", "mean6",
    "trend", "dev_from_mean", "cv_personal", "n_recorded",
]

# Conservative configs tuned for small-per-user datasets.
# Shallow trees and high min_child_weight prevent overfitting to individual user patterns.
CANDIDATES = {
    "XGBoost": XGBRegressor(
        n_estimators=400,
        learning_rate=0.03,
        max_depth=4,
        subsample=0.75,
        colsample_bytree=0.75,
        min_child_weight=5,
        reg_alpha=0.1,
        reg_lambda=2,
        verbosity=0,
        random_state=42,
        n_jobs=-1,
    ),
    "LightGBM": LGBMRegressor(
        n_estimators=400,
        learning_rate=0.03,
        num_leaves=20,
        subsample=0.75,
        colsample_bytree=0.75,
        min_child_samples=20,
        reg_alpha=0.1,
        reg_lambda=2,
        verbose=-1,
        random_state=42,
        n_jobs=-1,
    ),
    "GradientBoosting": GradientBoostingRegressor(
        n_estimators=400,
        learning_rate=0.03,
        max_depth=3,
        subsample=0.75,
        min_samples_leaf=10,
        random_state=42,
    ),
    "RandomForest": RandomForestRegressor(
        n_estimators=400,
        max_depth=8,
        min_samples_leaf=5,
        max_features=0.7,
        random_state=42,
        n_jobs=-1,
    ),
    "BayesianRidge": Pipeline([
        ("scaler", StandardScaler()),
        ("model", BayesianRidge()),
    ]),
}


def run_cv(X_train, y_train, groups_train) -> dict[str, float]:
    cv = GroupKFold(n_splits=5)
    results = {}
    for name, model in CANDIDATES.items():
        scores = cross_val_score(
            model, X_train, y_train,
            cv=cv,
            groups=groups_train,
            scoring="neg_mean_absolute_error",
            n_jobs=1,
        )
        results[name] = -scores.mean()
        print(f"  {name:<20} CV-MAE: {results[name]:.4f} (+/- {scores.std():.4f})")
    return results


def main():
    print("Loading data...")
    df = load_and_clean(DATA_PATH)
    print(f"  {len(df)} rows, {df['new_id'].nunique()} users")

    print("Building consecutive pairs...")
    pairs = build_pairs(df)
    print(f"  {len(pairs)} valid pairs")

    print("Engineering features...")
    features_df = engineer_features(pairs)
    print(f"  {len(features_df)} rows, {len(FEATURE_COLS)} features")

    X = features_df[FEATURE_COLS].values
    y = features_df["next_cycle_length"].values
    groups = features_df["user_id"].values

    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    groups_train = groups[train_idx]

    print(f"  Train: {len(X_train)} rows / {len(np.unique(groups_train))} users")
    print(f"  Test:  {len(X_test)} rows / {len(np.unique(groups[test_idx]))} users")

    print("Cross-validating (5-fold GroupKFold)...")
    cv_results = run_cv(X_train, y_train, groups_train)

    best_name = min(cv_results, key=cv_results.get)
    best_model = CANDIDATES[best_name]
    print(f"\nSelected: {best_name} (CV-MAE = {cv_results[best_name]:.4f})")

    print("Fitting on full train set...")
    best_model.fit(X_train, y_train)

    y_pred = np.clip(best_model.predict(X_test), 15, 60)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    naive_mae = mean_absolute_error(
        y_test, X_test[:, FEATURE_COLS.index("cycle_length")]
    )
    mean_mae = mean_absolute_error(y_test, np.full_like(y_test, y_train.mean()))

    print(f"\nHold-out results ({len(np.unique(groups[test_idx]))} unseen users):")
    print(f"  MAE  : {mae:.4f} days")
    print(f"  RMSE : {rmse:.4f} days")
    print(f"  R2   : {r2:.4f}")
    print(f"  Naive baseline (prev=next) : {naive_mae:.4f}")
    print(f"  Mean baseline              : {mean_mae:.4f}")
    print(f"  Improvement over naive     : {naive_mae - mae:.4f} days")

    # Feature importances (tree-based models)
    underlying = best_model
    if hasattr(best_model, "named_steps"):
        underlying = best_model.named_steps.get("model", best_model)
    if hasattr(underlying, "feature_importances_"):
        pairs_imp = sorted(
            zip(FEATURE_COLS, underlying.feature_importances_), key=lambda x: -x[1]
        )
        print("\nFeature importances (top 8):")
        for feat, imp in pairs_imp[:8]:
            print(f"  {feat:<18}: {imp * 100:.1f}%")

    global_stats = {"mean": float(y_train.mean()), "std": float(y_train.std())}

    joblib.dump(best_model, MODEL_DIR / "siklika_model.pkl")
    joblib.dump(FEATURE_COLS, MODEL_DIR / "feature_cols.pkl")
    joblib.dump(global_stats, MODEL_DIR / "global_stats.pkl")

    print(f"\nSaved: {MODEL_DIR}")
    print(f"Final model: {best_name}, MAE = {mae:.4f} days")


if __name__ == "__main__":
    main()
