"""Offline training and evaluation for the controlled demonstration dataset."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.cluster import DBSCAN, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from app.ml.dataset import SEED

ORDER_FEATURES = (
    "width_mm",
    "height_mm",
    "depth_mm",
    "accessory_count",
    "item_count",
    "complexity_score",
    "workshop_load",
    "quoted_total_minor",
    "promised_days",
    "customer_frequency",
    "category",
    "material",
    "district",
)
NUMERIC_COUNT = 10
CUSTOMER_FEATURES = (
    "customer_recency_days",
    "customer_frequency",
    "customer_total_spend_minor",
    "customer_avg_ticket_minor",
    "categories_bought",
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 500:
        raise ValueError("Se esperaban exactamente 500 pedidos sintéticos.")
    return rows


def _order_matrix(rows: list[dict[str, str]]) -> list[list[object]]:
    result: list[list[object]] = []
    for row in rows:
        result.append(
            [float(row[name]) if name in ORDER_FEATURES[:NUMERIC_COUNT] else row[name]
             for name in ORDER_FEATURES]
        )
    return result


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [("numeric", numeric, list(range(NUMERIC_COUNT))),
         ("categorical", categorical, list(range(NUMERIC_COUNT, len(ORDER_FEATURES))))]
    )


def _pipeline(estimator: object) -> Pipeline:
    return Pipeline([("prepare", _preprocessor()), ("model", estimator)])


def _regression_metrics(expected: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": round(float(mean_absolute_error(expected, predicted)), 5),
        "rmse": round(float(root_mean_squared_error(expected, predicted)), 5),
        "r2": round(float(r2_score(expected, predicted)), 5),
    }


def _classification_metrics(
    expected: np.ndarray, predicted: np.ndarray, probability: np.ndarray
) -> dict[str, object]:
    return {
        "accuracy": round(float(accuracy_score(expected, predicted)), 5),
        "precision": round(float(precision_score(expected, predicted, zero_division=0)), 5),
        "recall": round(float(recall_score(expected, predicted, zero_division=0)), 5),
        "f1": round(float(f1_score(expected, predicted, zero_division=0)), 5),
        "rocAuc": round(float(roc_auc_score(expected, probability)), 5),
        "brierLoss": round(float(brier_score_loss(expected, probability)), 5),
        "confusionMatrix": confusion_matrix(expected, predicted).tolist(),
    }


def _artifact_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _train_supervised(
    rows: list[dict[str, str]], artifact_dir: Path, seed: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    features = _order_matrix(rows)
    regression_target = np.asarray([float(row["production_days"]) for row in rows])
    classification_target = np.asarray([int(row["is_delayed"]) for row in rows])
    indexes = np.arange(len(rows))
    train_indexes, temp_indexes = train_test_split(
        indexes,
        test_size=0.30,
        random_state=seed,
        stratify=classification_target,
    )
    validation_indexes, test_indexes = train_test_split(
        temp_indexes,
        test_size=0.50,
        random_state=seed,
        stratify=classification_target[temp_indexes],
    )
    train_validation_indexes = np.concatenate((train_indexes, validation_indexes))

    def subset(values: list[list[object]], selected: np.ndarray) -> list[list[object]]:
        return [values[int(index)] for index in selected]

    regression_candidates = {
        "linear_regression": _pipeline(LinearRegression()),
        "decision_tree": _pipeline(
            DecisionTreeRegressor(max_depth=7, min_samples_leaf=5, random_state=seed)
        ),
        "random_forest": _pipeline(
            RandomForestRegressor(
                n_estimators=160,
                max_depth=9,
                min_samples_leaf=3,
                random_state=seed,
                n_jobs=-1,
            )
        ),
    }
    regression_baseline = _pipeline(DummyRegressor(strategy="median"))
    regression_baseline.fit(subset(features, train_indexes), regression_target[train_indexes])
    regression_baseline_metrics = _regression_metrics(
        regression_target[validation_indexes],
        regression_baseline.predict(subset(features, validation_indexes)),
    )
    regression_validation: dict[str, dict[str, float]] = {}
    for name, model in regression_candidates.items():
        model.fit(subset(features, train_indexes), regression_target[train_indexes])
        regression_validation[name] = _regression_metrics(
            regression_target[validation_indexes],
            model.predict(subset(features, validation_indexes)),
        )
    regression_name = min(
        regression_validation, key=lambda name: regression_validation[name]["mae"]
    )
    regression_model = clone(regression_candidates[regression_name])
    regression_model.fit(
        subset(features, train_validation_indexes), regression_target[train_validation_indexes]
    )
    regression_test = _regression_metrics(
        regression_target[test_indexes], regression_model.predict(subset(features, test_indexes))
    )
    regression_baseline.fit(
        subset(features, train_validation_indexes), regression_target[train_validation_indexes]
    )
    regression_baseline_test = _regression_metrics(
        regression_target[test_indexes],
        regression_baseline.predict(subset(features, test_indexes)),
    )
    if regression_test["mae"] >= regression_baseline_test["mae"]:
        raise RuntimeError("El modelo de regresión no superó la línea base.")

    classification_candidates = {
        "logistic_regression": _pipeline(
            LogisticRegression(max_iter=2_000, class_weight="balanced", random_state=seed)
        ),
        "knn": _pipeline(KNeighborsClassifier(n_neighbors=15, weights="distance")),
        "svm": _pipeline(
            CalibratedClassifierCV(
                SVC(class_weight="balanced", random_state=seed, C=1.2),
                method="sigmoid",
                cv=3,
            )
        ),
        "decision_tree": _pipeline(
            DecisionTreeClassifier(
                max_depth=6, min_samples_leaf=8, class_weight="balanced", random_state=seed
            )
        ),
    }
    classification_baseline = _pipeline(DummyClassifier(strategy="prior"))
    classification_baseline.fit(
        subset(features, train_indexes), classification_target[train_indexes]
    )
    baseline_probability = classification_baseline.predict_proba(
        subset(features, validation_indexes)
    )[:, 1]
    classification_baseline_metrics = _classification_metrics(
        classification_target[validation_indexes],
        classification_baseline.predict(subset(features, validation_indexes)),
        baseline_probability,
    )
    classification_validation: dict[str, dict[str, object]] = {}
    for name, model in classification_candidates.items():
        model.fit(subset(features, train_indexes), classification_target[train_indexes])
        validation_features = subset(features, validation_indexes)
        classification_validation[name] = _classification_metrics(
            classification_target[validation_indexes],
            model.predict(validation_features),
            model.predict_proba(validation_features)[:, 1],
        )
    classification_name = max(
        classification_validation,
        key=lambda name: float(classification_validation[name]["f1"]),
    )
    classification_model = clone(classification_candidates[classification_name])
    classification_model.fit(
        subset(features, train_validation_indexes), classification_target[train_validation_indexes]
    )
    test_features = subset(features, test_indexes)
    classification_test = _classification_metrics(
        classification_target[test_indexes],
        classification_model.predict(test_features),
        classification_model.predict_proba(test_features)[:, 1],
    )
    classification_baseline.fit(
        subset(features, train_validation_indexes),
        classification_target[train_validation_indexes],
    )
    classification_baseline_test = _classification_metrics(
        classification_target[test_indexes],
        classification_baseline.predict(test_features),
        classification_baseline.predict_proba(test_features)[:, 1],
    )
    if float(classification_test["f1"]) <= float(classification_baseline_test["f1"]):
        raise RuntimeError("El modelo de clasificación no superó la línea base.")

    regression_path = artifact_dir / "production_days_v1.joblib"
    classification_path = artifact_dir / "delay_risk_v1.joblib"
    joblib.dump(regression_model, regression_path, compress=3)
    joblib.dump(classification_model, classification_path, compress=3)
    regression_entry = {
        "problem": "production_days",
        "algorithm": regression_name,
        "version": 1,
        "artifactPath": f"artifacts/ml/{regression_path.name}",
        "artifactHash": _artifact_hash(regression_path),
        "features": list(ORDER_FEATURES),
        "parameters": regression_model.named_steps["model"].get_params(),
        "metrics": {
            "baselineValidation": regression_baseline_metrics,
            "baselineTest": regression_baseline_test,
            "candidateValidation": regression_validation,
            "test": regression_test,
            "split": {"train": 350, "validation": 75, "test": 75},
        },
    }
    classification_entry = {
        "problem": "delay_risk",
        "algorithm": classification_name,
        "version": 1,
        "artifactPath": f"artifacts/ml/{classification_path.name}",
        "artifactHash": _artifact_hash(classification_path),
        "features": list(ORDER_FEATURES),
        "parameters": classification_model.named_steps["model"].get_params(),
        "metrics": {
            "baselineValidation": classification_baseline_metrics,
            "baselineTest": classification_baseline_test,
            "candidateValidation": classification_validation,
            "test": classification_test,
            "split": {"train": 350, "validation": 75, "test": 75},
        },
    }
    return regression_entry, classification_entry


def _train_clustering(
    rows: list[dict[str, str]], artifact_dir: Path, seed: int
) -> dict[str, Any]:
    by_customer: dict[str, dict[str, str]] = {}
    for row in rows:
        by_customer[row["customer_id"]] = row
    customer_matrix = np.asarray(
        [[float(row[name]) for name in CUSTOMER_FEATURES] for row in by_customer.values()]
    )
    scaled = StandardScaler().fit_transform(customer_matrix)
    algorithms = {
        "kmeans": KMeans(n_clusters=4, n_init=20, random_state=seed),
        "dbscan": DBSCAN(eps=0.95, min_samples=5),
    }
    comparison: dict[str, dict[str, float | int | None]] = {}
    for name, algorithm in algorithms.items():
        labels = algorithm.fit_predict(scaled)
        usable = labels != -1
        cluster_count = len(set(labels[usable]))
        noise_count = int(np.sum(labels == -1))
        if cluster_count >= 2 and int(np.sum(usable)) > cluster_count:
            comparison[name] = {
                "clusters": cluster_count,
                "noisePoints": noise_count,
                "silhouette": round(float(silhouette_score(scaled[usable], labels[usable])), 5),
                "daviesBouldin": round(
                    float(davies_bouldin_score(scaled[usable], labels[usable])), 5
                ),
            }
        else:
            comparison[name] = {
                "clusters": cluster_count,
                "noisePoints": noise_count,
                "silhouette": None,
                "daviesBouldin": None,
            }
    selected = "kmeans"
    model = Pipeline(
        [("scale", StandardScaler()), ("model", KMeans(n_clusters=4, n_init=20, random_state=seed))]
    )
    model.fit(customer_matrix)
    artifact_path = artifact_dir / "customer_segments_v1.joblib"
    joblib.dump(model, artifact_path, compress=3)
    return {
        "problem": "customer_segments",
        "algorithm": selected,
        "version": 1,
        "artifactPath": f"artifacts/ml/{artifact_path.name}",
        "artifactHash": _artifact_hash(artifact_path),
        "features": list(CUSTOMER_FEATURES),
        "parameters": {"nClusters": 4, "randomSeed": seed},
        "metrics": {"comparison": comparison, "customers": len(by_customer)},
    }


def train_all(dataset_path: Path, artifact_dir: Path, seed: int = SEED) -> dict[str, Any]:
    """Train every planned model and write a machine-readable manifest."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_rows(dataset_path)
    regression, classification = _train_supervised(rows, artifact_dir, seed)
    clustering = _train_clustering(rows, artifact_dir, seed)
    manifest = {
        "dataLabel": "Datos de prueba",
        "dataset": "data/synthetic/orders_v1.csv",
        "rows": len(rows),
        "randomSeed": seed,
        "models": [regression, classification, clustering],
    }
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return manifest
