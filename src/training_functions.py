import numpy as np
import pandas as pd
import joblib
from tqdm import tqdm
from matplotlib import pyplot as plt
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier # type: ignore


def split_feature_df(feature_df):
    non_noise_feature_df = feature_df[feature_df["label"] != 101]

    X = non_noise_feature_df.drop(columns = ["label", "subject_id"])

    y = non_noise_feature_df["label"]

    groups = non_noise_feature_df["subject_id"]

    return X, y, groups

def find_best_model(
    X,
    y,
    groups,
    scoring_metric = 'f1_macro',
    random_state = 0,
    k_neighbors = 5,
    save_pca_jpg = True,
    output_filepath = "best_model_pca_plot.jpg",
    n_jobs = -1
):
    # Cap k-neighbors based on global minority class count
    min_samples = np.min(np.bincount(y))
    effective_k = max(1, min(k_neighbors, min_samples - 1))

    # Candidate models
    classifiers = {
        "RandomForest": RandomForestClassifier(
            n_estimators = 100, random_state = random_state, n_jobs = n_jobs
        ),
        "ExtraTrees": ExtraTreesClassifier(
            n_estimators = 100, random_state = random_state, n_jobs = n_jobs
        ), 
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators = 100, random_state = random_state
        ),
        "XGBoost": XGBClassifier(
            n_estimators = 100, eval_metric = "mlogloss", random_state = random_state, n_jobs = n_jobs
        ),
        "KNN": KNeighborsClassifier(n_neighbors = 5, n_jobs = n_jobs)
    }

    logo = LeaveOneGroupOut()
    results = []
    fitted_pipelines = {}

    for name, clf in tqdm(classifiers.items()):
        pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("smote",
                 SMOTE(k_neighbors = effective_k, random_state = random_state)),
                 ("classifier", clf)
            ]
        )

        oof_predictions = np.zeros(len(y))

        # LOGO CV
        for i, (train_idx, val_idx) in tqdm(enumerate(logo.split(X, y, groups = groups))):
            print(f"Train loop #{i + 1}")
            X_train, X_val = (
                X.iloc[train_idx] if hasattr(X, "iloc") else X[train_idx],
                X.iloc[val_idx] if hasattr(X, "iloc") else X[val_idx]
            )
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            print("Fitting pipeline...")
            pipeline.fit(X_train, y_train)

            oof_predictions[val_idx] = pipeline.predict(X_val)
        
        # OOF metrics
        print(f"Calculating metrics for {name} classifier")
        acc = accuracy_score(y, oof_predictions)
        f1_macro = f1_score(y, oof_predictions, average = 'macro')
        f1_weighted = f1_score(y, oof_predictions, average = 'weighted')

        results.append(
            {
                "Model": name,
                "Accuracy": acc,
                "F1 Macro": f1_macro,
                "F1 Weighted": f1_weighted
            }
        )

        fitted_pipelines[name] = pipeline

    metric_map = {
        "f1_macro": "F1 Macro",
        "f1_weighted": "F1 Weighted",
        "accuracy": "Accuracy"
    }

    sort_col = metric_map.get(scoring_metric.lower(), "F1 Macro")

    comparison_df = pd.DataFrame(results).sort_values(
        by = sort_col, ascending = False
    )

    best_model_name = comparison_df.iloc[0]["Model"]
    best_pipeline = fitted_pipelines[best_model_name]

    print("Model Pipeline Comparison Report")
    print(comparison_df.to_string(index = False))
    print(f"Best Pipeline: {best_model_name} based on {scoring_metric}")

    if save_pca_jpg:
        scaler = best_pipeline.named_steps["scaler"]
        X_scaled = scaler.transform(X)

        pca = PCA(n_components = 2, random_state = random_state)
        X_pca = pca.fit_transform(X_scaled)

        var_exp = pca.explained_variance_ratio_ * 100

        plt.figure(figsize = (8, 6), dpi = 600)
        scatter = plt.scatter(
            X_pca[:, 0],
            X_pca[:, 1],
            c = y,
            cmap = "viridis",
            alpha = 0.5,
            edgecolors = "k",
            linewidth = 0.5
        )

        plt.title(
            f"2D PCA Projection: {best_model_name} Features",
            fontsize = 12,
            fontweight = "bold"
        )
        plt.xlabel(f"PC1: ({var_exp[0]:.1f}% Variance)")
        plt.ylabel(f"PC2: ({var_exp[1]:.1f}% Variance)")
        plt.colorbar(scatter, label = "Exertion Class / Label")
        plt.grid(True, linestyle = "--", alpha = 0.5)

        plt.savefig(output_filepath, format = 'jpg', bbox_inches = "tight", dpi = 600)
        plt.close()

    return best_pipeline, comparison_df


def use_best_model(
    X,
    y,
    groups,
    model = 'GradientBoosting',
    random_state = 0,
    k_neighbors = 5
):

    # Cap k-neighbors based on global minority class count
    min_samples = np.min(np.bincount(y))
    effective_k = max(1, min(k_neighbors, min_samples - 1))

    # Models
    classifiers = {
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators = 100, random_state = random_state
        )
    }

    logo = LeaveOneGroupOut()
    results = []
    fitted_pipelines = {}

    for name, clf in classifiers.items():
        pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("smote",
                 SMOTE(k_neighbors = effective_k, random_state = random_state)),
                 ("classifier", clf)
            ]
        )

        oof_predictions = np.zeros(len(y))

        # LOGO CV
        for i, (train_idx, val_idx) in tqdm(enumerate(logo.split(X, y, groups = groups))):
            print(f"Train loop #{i + 1}")
            X_train, X_val = (
                X.iloc[train_idx] if hasattr(X, "iloc") else X[train_idx],
                X.iloc[val_idx] if hasattr(X, "iloc") else X[val_idx]
            )
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            print("Fitting pipeline...")
            pipeline.fit(X_train, y_train)

            oof_predictions[val_idx] = pipeline.predict(X_val)
        
        # OOF metrics
        print(f"Calculating metrics for {name} classifier")
        acc = accuracy_score(y, oof_predictions)
        f1_macro = f1_score(y, oof_predictions, average = 'macro')
        f1_weighted = f1_score(y, oof_predictions, average = 'weighted')

        results.append(
            {
                "Model": name,
                "Accuracy": acc,
                "F1 Macro": f1_macro,
                "F1 Weighted": f1_weighted
            }
        )

        fitted_pipelines[name] = pipeline

    sort_col = "F1 Macro"

    comparison_df = pd.DataFrame(results).sort_values(
        by = sort_col, ascending = False
    )

    best_model_name = comparison_df.iloc[0]["Model"]
    best_pipeline = fitted_pipelines[best_model_name]

    joblib.dump(best_pipeline, "best_exertion_pipeline.joblib")
    print("Model pipeline successfully saved to best_exertion_pipeline.joblib")

    print("Model Pipeline Comparison Report")
    print(comparison_df.to_string(index = False))

    return
