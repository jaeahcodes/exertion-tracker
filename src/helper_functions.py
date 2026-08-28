import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import find_peaks, butter, filtfilt
from statsmodels.tsa.ar_model import AutoReg


# VARIABLES
filter_specs = {
        "accel": {
            "type": "low",
            "fc": 12
        },
        "gyro": {
            "type": "low",
            "fc": 12
        },
        "magnet": {
            "type": "low",
            "fc": 2
        },
        "ecg": {
            "type": "band",
            "fc": [0.5, 24]
        }
    } 
qrs_refrac_time = 200 # ms
n_samp_qrs_refrac = round(qrs_refrac_time * 50 / 1000.)

# 1. Applying Butterworth Filter
def apply_butterworth(data, filter_type, fc, fs = 50):
    nyq = 0.5 * fs

    if isinstance(fc, list):
        normal_cutoff = [c / nyq for c in fc]
    else: 
        normal_cutoff = fc / nyq

    b, a = butter(N = 4, Wn = normal_cutoff, btype = filter_type, analog = False)
    y = filtfilt(b, a, data)
    return y

def preprocess_full_df(ref_df, fs = 50):
    """
    Processes subject by subject to prevent signal bleeding between subjects.
    """
    for sensor, specs in filter_specs.items():
        cols = [col for col in ref_df.columns if sensor in col]
        for col in cols: 
            filtered_signal = apply_butterworth(ref_df[col], specs["type"], specs["fc"], fs)

            if "ecg" in col:
                mean = filtered_signal.mean()
                std = filtered_signal.std()

                ref_df[f"{col}_filt"] = filtered_signal / np.max(np.abs(filtered_signal))
            else:
                ref_df[f"{col}_filt"] = filtered_signal
    
    return ref_df

def window_generator(df, window_size = 250, step_size = 125):
    """
    Function yields chunks of the dataframe by subject and by activity.
    """
    for subject_id in df["subject_id"].unique():
        subj_df = df[df["subject_id"] == subject_id].reset_index()

        for activity_label in subj_df["activity_label"].unique():
            subj_activity_df = subj_df[subj_df["activity_label"] == activity_label].reset_index()

            if len(subj_activity_df) < window_size: 
                continue

            for start in range(0, len(subj_activity_df) - window_size + 1, step_size):
                yield subj_activity_df.iloc[start : start + window_size]

# 2. Label Engineering
def calculate_tilt(window, sensor):    
    x = window[f"x_{sensor}_filt"].mean()
    y = window[f"y_{sensor}_filt"].mean()
    z = window[f"z_{sensor}_filt"].mean()

    mag = np.sqrt(x**2 + y**2 + z**2)

    if mag == 0:
        return 0
    
    tilt = np.degrees(np.arccos(np.clip(y / mag, -1.0, 1.0)))

    return tilt

def extract_ar_coeffs(window, sensor, order = 3):
    if (len(window[sensor]) <= order) or (np.std(window[sensor]) < 1e-6):
        return [0.0] * order
    
    try:
        model = AutoReg(window[sensor], lags = order).fit()
        return model.params[1:]
    
    except:
        return np.nan

def consolidate_bpm(df):
    df["bpm_final"] = df["bpm_l1"]

    l2_is_healthy = (df["bpm_l2"] > 52) & (df["bpm_l2"].notna())
    l1_is_healthy = (df["bpm_l1"] > 52) & (df["bpm_l1"].notna())

    df.loc[l1_is_healthy & l2_is_healthy, "bpm_final"] = (df["bpm_l1"] + df["bpm_l2"]) / 2

    # If L1 failed but L2 is good:
    df.loc[~l1_is_healthy & l2_is_healthy, "bpm_final"] = df["bpm_l2"]

    df["bpm_final"] = df["bpm_final"].fillna(70)

    return df

def extract_hr_features(df, fs = 50, threshold = [1.05, 1.02]):
    """
    Extracts HR from ECG measurements subject by subject to prevent signal bleeding between subjects.
    """
    df = df.copy()

    qrs_refrac_time = 200 # ms
    n_samp_qrs_refrac = round(qrs_refrac_time * fs / 1000.)

    for i, lead in enumerate(["ecg_l1_filt", "ecg_l2_filt"]):
        bpm_col = f"bpm_{lead.split('_')[-2]}"

        signal = np.abs(df[lead])

        th = signal.mean() + (threshold[i] * signal.std())

        peaks, _ = find_peaks(signal, height = th, distance = n_samp_qrs_refrac)

        if len(peaks) > 1: 
            rr_seconds = np.diff(peaks) / fs
            hr_values = 60 / rr_seconds

            hr_values = np.clip(hr_values, 50, 220)

            df[bpm_col] = np.nan

            df.iloc[peaks[1:], df.columns.get_loc(bpm_col)] = hr_values

            df[bpm_col] = df[bpm_col].interpolate(method = "linear").ffill().bfill()
        
        else:
            df[bpm_col] = np.nan

    return consolidate_bpm(df)

def plot_ecg_signal(time, signal):
    fig = plt.figure(figsize = (20, 3))
    ax = plt.axes()
    ax.plot(time, signal)
    min_t = int(np.min(time))
    max_t = int(np.max(time))
    major_ticks = np.arange(min_t, max_t + 1, 50)
    ax.set_xticks(major_ticks)
    ax.grid(which = "major", linestyle = "-", color = "red", linewidth = "0.5")
    plt.xlabel("Time")
    plt.ylabel("Amplitude")
    return ax

def find_r_peaks(time, signal, threshold=0.6, distance=n_samp_qrs_refrac):
    smax = np.max(signal)
    smin = np.min(signal)
    srange = smax - smin
    th = srange * threshold + smin
    r_peaks, _ = find_peaks(signal > th, height=0, distance=distance)
    peak_times = time[r_peaks]
    peak_values = signal[r_peaks]
    return peak_times, peak_values

def calculate_sma(window_df, sensor):
    cols = [c for c in window_df.columns if sensor in c and any(a in c for a in ["x_", "y_", "z_"]) and any(b in c for b in ["_filt"])]

    sma = window_df[cols].abs().sum(axis = 1).mean()

    return sma

def calculate_subject_baselines(df, rest_labels = [1, 2, 3]):
    baselines = {}

    for subject_id in df["subject_id"].unique():
        rest_data = df[
            (df["subject_id"] == subject_id) & 
            (df["activity_label"].isin(rest_labels))
        ]

        if not rest_data.empty:
            baselines[subject_id] = rest_data["bpm_l1"].quantile(0.1)
        else:
            baselines[subject_id] = df["bpm_l1"].quantile(0.1)
    
    return baselines

def create_feature_df(df_hr_extracted, sma_threshold = 25, hr_delta_threshold = 25):
    subject_baselines = calculate_subject_baselines(df_hr_extracted)
    feature_rows = []

    for window in window_generator(df_hr_extracted):
        subject = window["subject_id"].iloc[0]
        original_label = window["activity_label"].iloc[0]
        avg_l1_bpm = window["bpm_l1"].mean()
        avg_l2_bpm = window["bpm_l2"].mean()
        avg_bpm = (avg_l1_bpm + avg_l2_bpm) / 2
        hr_elevation = avg_bpm - subject_baselines.get(subject, 70)

        motion_sma = calculate_sma(window, "accel_l_ankle")

        chest_accel_ta = calculate_tilt(window, "accel_chest")
        ankle_accel_ta = calculate_tilt(window, "accel_l_ankle")
        arm_accel_ta = calculate_tilt(window, "accel_r_arm")

        chest_accel_sma = calculate_sma(window, "accel_chest")
        ankle_accel_sma = motion_sma
        arm_accel_sma = calculate_sma(window, "accel_r_arm")

        ankle_gyro_sma = calculate_sma(window, "gyro_l_ankle")
        arm_gyro_sma = calculate_sma(window, "gyro_r_arm")

        chest_x_ar_features = extract_ar_coeffs(window, "x_accel_chest_filt")
        chest_y_ar_features = extract_ar_coeffs(window, "y_accel_chest_filt")
        chest_z_ar_features = extract_ar_coeffs(window, "z_accel_chest_filt")
        ankle_x_ar_features = extract_ar_coeffs(window, "x_accel_l_ankle_filt")
        ankle_y_ar_features = extract_ar_coeffs(window, "y_accel_l_ankle_filt")
        ankle_z_ar_features = extract_ar_coeffs(window, "z_accel_l_ankle_filt")
        arm_x_ar_features = extract_ar_coeffs(window, "x_accel_r_arm_filt")
        arm_y_ar_features = extract_ar_coeffs(window, "y_accel_r_arm_filt")
        arm_z_ar_features = extract_ar_coeffs(window, "z_accel_r_arm_filt")


        if original_label == 0:
            is_motion_high = motion_sma > sma_threshold
            is_hr_high = hr_elevation > hr_delta_threshold

            if not is_motion_high and not is_hr_high:
                new_label = 0 # Baseline
            elif is_motion_high and not is_hr_high:
                new_label = 101 # Sensor Noise
            elif not is_motion_high and is_hr_high:
                new_label = 13 # Recovery
            elif is_motion_high and is_hr_high:
                new_label = 14 # Active Exertion
        
        else:
            new_label = original_label

        features = {
            # Identifiers
            "subject_id": subject,
            "label": new_label,

            # Physiology 
            "avg_bpm": avg_bpm,
            "hr_elevation": hr_elevation,

            # Tilt
            "chest_accel_ta": chest_accel_ta,
            "ankle_accel_ta": ankle_accel_ta,
            "arm_accel_ta": arm_accel_ta,

            # AR Coefficients (only on accelerator measurements)
            "ar_1": chest_x_ar_features.iloc[0],
            "ar_2": chest_x_ar_features.iloc[1],
            "ar_3": chest_x_ar_features.iloc[2],
            "ar_4": chest_y_ar_features.iloc[0],
            "ar_5": chest_y_ar_features.iloc[1],
            "ar_6": chest_y_ar_features.iloc[2],
            "ar_7": chest_z_ar_features.iloc[0],
            "ar_8": chest_z_ar_features.iloc[1],
            "ar_9": chest_z_ar_features.iloc[2],

            "ar_10": ankle_x_ar_features.iloc[0],
            "ar_11": ankle_x_ar_features.iloc[1],
            "ar_12": ankle_x_ar_features.iloc[2],
            "ar_13": ankle_y_ar_features.iloc[0],
            "ar_14": ankle_y_ar_features.iloc[1],
            "ar_15": ankle_y_ar_features.iloc[2],
            "ar_16": ankle_z_ar_features.iloc[0],
            "ar_17": ankle_z_ar_features.iloc[1],
            "ar_18": ankle_z_ar_features.iloc[2],

            "ar_19": arm_x_ar_features.iloc[0],
            "ar_20": arm_x_ar_features.iloc[1],
            "ar_21": arm_x_ar_features.iloc[2],
            "ar_22": arm_y_ar_features.iloc[0],
            "ar_23": arm_y_ar_features.iloc[1],
            "ar_24": arm_y_ar_features.iloc[2],
            "ar_25": arm_z_ar_features.iloc[0],
            "ar_26": arm_z_ar_features.iloc[1],
            "ar_27": arm_z_ar_features.iloc[2],

            # Intensity (SMA)
            "chest_accel_sma": chest_accel_sma,
            "ankle_accel_sma": ankle_accel_sma,
            "arm_accel_sma": arm_accel_sma,

            "ankle_gyro_sma":  ankle_gyro_sma,
            "arm_gyro_sma": arm_gyro_sma,

            # Variance
            "chest_x_accel_std": window["x_accel_chest_filt"].std(),
            "chest_y_accel_std": window["y_accel_chest_filt"].std(),
            "chest_z_accel_std": window["z_accel_chest_filt"].std(),

            "ankle_x_accel_std": window["x_accel_l_ankle_filt"].std(),
            "ankle_y_accel_std": window["y_accel_l_ankle_filt"].std(),
            "ankle_z_accel_std": window["z_accel_l_ankle_filt"].std(),

            "arm_x_accel_std": window["x_accel_r_arm_filt"].std(),
            "arm_y_accel_std": window["y_accel_r_arm_filt"].std(),
            "arm_z_accel_std": window["z_accel_r_arm_filt"].std(),
        }

        feature_rows.append(features)

    return pd.DataFrame(feature_rows)