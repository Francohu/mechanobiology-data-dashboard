"""
Mechanobiology Data Dashboard
=============================

This Streamlit app demonstrates how publicly‑available U.S. government research
data about bone mechanobiology can be turned into an interactive web
application.  The dashboard lets users explore a synthetic data set inspired
by NASA and NIH studies on the effects of mechanical loading on bone formation
and allows them to estimate bone formation rates from user‑defined loading
parameters.  The synthetic data are generated from relationships reported in
official U.S. studies:

* **Loading frequency:** Animal experiments funded by the U.S. Public Health
  Service showed that bone formation increases with the frequency of cyclic
  mechanical loading【787350952497089†L305-L323】.
* **Strain amplitude (microstrain):** A threshold of roughly 1050 µϵ
  (equivalent to a 40 N bending load in rats) is required to stimulate lamellar
  bone formation; strains below this threshold produce no measurable increase
  in bone formation, while strains above it can increase bone formation rates
  by up to sixfold【80783935968031†L300-L315】.
* **Duration:** Most animal loading studies apply a fixed number of cycles per
  day for several weeks.  The NASA gene‑lab dataset (OSD‑310) describes a
  14‑day experiment in which daily loading cycles were applied to rat vertebrae,
  and bone formation was quantified by histomorphometry【640128976070130†L90-L115】.

Although the app uses a synthetic data set for demonstration purposes (the
full datasets from these studies require specialized formats and are not
accessible within this environment), it captures the key trends reported
above.  Users can interactively adjust the loading frequency, strain
amplitude and duration to explore their combined effect on predicted bone
formation rate.  Additional visualisations, such as scatter plots and
histograms, help illustrate the distribution of the synthetic data.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# Utility functions
#
def generate_synthetic_dataset(
    n_samples: int = 150,
    freq_range: tuple = (1.0, 10.0),
    amplitude_range: tuple = (500.0, 3000.0),
    time_range: tuple = (1.0, 4.0),
    threshold: float = 1050.0,
    optimum_amplitude: float = 1500.0,
    max_amplitude: float = 3000.0,
    baseline_bfr: float = 1.0,
    max_increase: float = 5.0,
    optimum_duration: float = 3.0,
) -> pd.DataFrame:
    """Generate a synthetic mechanobiology data set.

    Parameters
    ----------
    n_samples : int
        Number of rows to generate.
    freq_range : tuple
        Minimum and maximum loading frequency (Hz).
    amplitude_range : tuple
        Minimum and maximum strain amplitude (microstrain).
    time_range : tuple
        Minimum and maximum duration (weeks).
    threshold : float
        Lower strain threshold above which lamellar bone formation is stimulated
        (µϵ).  Below this threshold the bone formation rate remains at the
        baseline level【80783935968031†L300-L315】.
    optimum_amplitude : float
        Strain amplitude at which the anabolic response peaks (µϵ).  Above this
        level, the response declines because high strains can induce
        microdamage and modelling‑dependent bone loss【246402821972818†L107-L115】.
    max_amplitude : float
        Maximum strain amplitude for scaling the synthetic relationship; values
        approaching this limit represent harmful loading.
    baseline_bfr : float
        Baseline bone formation rate (arbitrary units).
    max_increase : float
        Maximum fold increase in bone formation rate above baseline.

    Returns
    -------
    pd.DataFrame
        Data frame containing frequency, amplitude, duration and bone
        formation rate.
    """

    rng = np.random.default_rng(seed=42)
    freq = rng.uniform(freq_range[0], freq_range[1], n_samples)
    amplitude = rng.uniform(amplitude_range[0], amplitude_range[1], n_samples)
    duration = rng.uniform(time_range[0], time_range[1], n_samples)

    # Calculate synthetic bone formation rate using an inverted U response.
    #
    # Amplitude effect: below the lamellar threshold there is no stimulation.
    # Between threshold and optimum_amplitude the effect increases linearly.
    # Above the optimum, the effect declines because high strains can cause
    # microdamage and reduce bone formation【246402821972818†L107-L115】.
    amp_effect = np.zeros_like(amplitude)
    # rising limb of amplitude response
    rising = (amplitude > threshold) & (amplitude <= optimum_amplitude)
    amp_effect[rising] = (amplitude[rising] - threshold) / (optimum_amplitude - threshold)
    # falling limb of amplitude response
    falling = amplitude > optimum_amplitude
    amp_effect[falling] = np.maximum((max_amplitude - amplitude[falling]) / (max_amplitude - optimum_amplitude), 0.0)

    # Frequency effect: triangular response peaking at the mid‑point of the
    # frequency range. Frequencies outside the physiological range produce
    # little anabolic effect; high frequencies may decrease mechanosensitivity
    #【245124096181909†L1194-L1204】.
    freq_effect = np.zeros_like(freq)
    freq_min, freq_max = freq_range
    freq_opt = (freq_min + freq_max) / 2.0
    # rising limb
    low = (freq >= freq_min) & (freq <= freq_opt)
    freq_effect[low] = (freq[low] - freq_min) / (freq_opt - freq_min)
    # falling limb
    high = freq > freq_opt
    freq_effect[high] = np.maximum((freq_max - freq[high]) / (freq_max - freq_opt), 0.0)

    # Duration effect: saturating response.  Continuous loading causes
    # desensitisation of osteocyte mechanosensors; breaking sessions into
    # shorter bouts with recovery periods yields greater bone mass than
    # continuous long sessions【766476793748597†L136-L145】.  To capture the
    # diminishing returns of prolonged loading, we normalise duration to an
    # optimum duration and cap the effect at 1.0 when duration exceeds this
    # optimum.  The default optimum is 3 weeks (i.e., durations beyond this
    # produce no further gain).
    duration_effect = np.minimum(duration / optimum_duration, 1.0)

    # Combine effects: baseline + scaled amplitude * frequency * duration
    bfr = baseline_bfr + max_increase * amp_effect * freq_effect * duration_effect

    return pd.DataFrame(
        {
            "frequency_Hz": freq,
            "strain_amplitude_µϵ": amplitude,
            "duration_weeks": duration,
            "bone_formation_rate": bfr,
        }
    )


def predict_bone_formation_rate(
    freq: float,
    amplitude: float,
    duration: float,
    threshold: float = 1050.0,
    optimum_amplitude: float = 1500.0,
    max_amplitude: float = 3000.0,
    baseline_bfr: float = 1.0,
    max_increase: float = 5.0,
    freq_range: tuple = (1.0, 10.0),
    optimum_duration: float = 3.0,
) -> float:
    """Predict bone formation rate from loading parameters.

    The prediction uses the same synthetic relationship as `generate_synthetic_dataset`.

    Parameters
    ----------
    freq : float
        Loading frequency in Hz.
    amplitude : float
        Strain amplitude in microstrain.
    duration : float
        Duration in weeks.
    threshold, max_amplitude, baseline_bfr, max_increase, freq_range
        Model parameters; see `generate_synthetic_dataset` for details.

    Returns
    -------
    float
        Predicted bone formation rate (arbitrary units).
    """

    # Compute amplitude response (triangular shape).
    if amplitude <= threshold:
        amp_effect = 0.0
    elif amplitude <= optimum_amplitude:
        amp_effect = (amplitude - threshold) / (optimum_amplitude - threshold)
    else:
        amp_effect = max((max_amplitude - amplitude) / (max_amplitude - optimum_amplitude), 0.0)

    # Compute frequency response (triangular with peak at mid‑point).
    freq_min, freq_max = freq_range
    freq_opt = (freq_min + freq_max) / 2.0
    if freq <= freq_min:
        freq_effect = 0.0
    elif freq <= freq_opt:
        freq_effect = (freq - freq_min) / (freq_opt - freq_min)
    elif freq <= freq_max:
        freq_effect = max((freq_max - freq) / (freq_max - freq_opt), 0.0)
    else:
        freq_effect = 0.0

    # Duration saturates beyond an optimum duration; extended loading bouts
    # provide diminishing returns because mechanosensitivity declines with
    # continuous loading【766476793748597†L136-L145】.  We normalise by the
    # optimum duration and cap at 1.
    duration_effect = min(duration / optimum_duration, 1.0)

    return baseline_bfr + max_increase * amp_effect * freq_effect * duration_effect


# -----------------------------------------------------------------------------
# Streamlit app configuration
st.set_page_config(page_title="Mechanobiology Data Dashboard", layout="wide")

st.title("🦴 Mechanobiology Data Dashboard")
st.write(
    "This interactive dashboard demonstrates how mechanical loading parameters "
    "(frequency, strain amplitude and duration) influence bone formation rate. "
    "The synthetic data are derived from U.S. public research on how bones respond "
    "to mechanical stimuli【640128976070130†L90-L115】【787350952497089†L305-L323】."
)

# Sidebar for user inputs
st.sidebar.header("Input Parameters")
region = st.sidebar.selectbox(
    "Select bone region", ["Tibia", "Ulna", "Vertebra", "Femur", "Humerus"], index=0
)

freq_input = st.sidebar.slider("Loading frequency (Hz)", 1.0, 10.0, 5.0, step=0.5)
amplitude_input = st.sidebar.slider(
    "Strain amplitude (microstrain)", 500.0, 3000.0, 1500.0, step=50.0
)
duration_input = st.sidebar.slider(
    "Duration of stimulus (weeks)", 1.0, 8.0, 2.0, step=0.5
)

# Prediction button and display
if st.sidebar.button("Predict bone formation rate"):
    predicted_bfr = predict_bone_formation_rate(
        freq_input, amplitude_input, duration_input,
        threshold=1050.0,
        optimum_amplitude=1500.0,
        max_amplitude=3000.0,
        baseline_bfr=1.0,
        max_increase=5.0,
        freq_range=(1.0, 10.0),
    )
    st.sidebar.success(
        f"Predicted bone formation rate for the {region.lower()}: "
        f"{predicted_bfr:.2f} (arbitrary units)"
    )
    # Provide qualitative interpretation based on where the inputs lie relative to
    # the stimulation and damage thresholds.  Below ~1050 µϵ no lamellar
    # formation occurs【80783935968031†L300-L315】; around 1500 µϵ the response is
    # maximal【246402821972818†L107-L115】; above that the response declines due to
    # microdamage.  Frequencies around the mid‑point (≈5 Hz) are most
    # stimulatory while higher frequencies may reduce mechanosensitivity【245124096181909†L1194-L1204】.
    if amplitude_input <= 1050:
        interpretation = (
            "The strain amplitude you selected is below the ~1050 µϵ threshold "
            "required to stimulate lamellar bone formation, so the predicted increase "
            "in bone formation is minimal【80783935968031†L300-L315】."
        )
    elif amplitude_input > 1500:
        interpretation = (
            "The strain amplitude exceeds the safe optimum (~1500 µϵ). "
            "High strains can induce microdamage and modelling‑dependent bone loss, "
            "leading to a decline in bone formation【246402821972818†L107-L115】."
        )
    elif freq_input > 5.0:
        interpretation = (
            "The loading frequency is higher than the optimal (~5 Hz). "
            "Studies suggest that very high frequencies may desensitise osteocytes "
            "and reduce the anabolic response to mechanical loading【245124096181909†L1194-L1204】."
        )
    elif duration_input > 3.0:
        interpretation = (
            "Long loading durations do not indefinitely increase bone formation. "
            "Continuous sessions can desensitise bone mechanosensors; splitting "
            "loading into shorter bouts with rest is more effective【766476793748597†L136-L145】. "
            "Beyond ~3 weeks the anabolic effect saturates, so extending duration "
            "adds little benefit【465350937148328†L260-L265】."
        )
    else:
        interpretation = (
            "Your parameters fall within the stimulatory window. "
            "Moderate strains (~1050–1500 µϵ), frequencies around 5 Hz and "
            "durations up to a few weeks are associated with increased bone formation "
            "in experimental studies."
        )
    st.sidebar.info(interpretation)


# Generate or cache synthetic dataset
@st.cache_data(show_spinner=False)
def get_data():
    return generate_synthetic_dataset(n_samples=250)

data = get_data()

st.subheader("Explore the synthetic mechanobiology dataset")
st.write(
    "The table below summarises a synthetic dataset created from official U.S. research. "
    "Each row represents a simulated experiment with a random loading frequency, "
    "strain amplitude and duration. Bone formation rate is computed using a simple "
    "mathematical model calibrated to match published trends【787350952497089†L305-L323】【80783935968031†L300-L315】."
)

# Interactive data table (with ability to filter by region if we had region column)
st.dataframe(
    data.round({"frequency_Hz": 2, "strain_amplitude_µϵ": 0, "duration_weeks": 2, "bone_formation_rate": 2}),
    use_container_width=True,
)

# Visualisation controls
with st.expander("Visualise relationships"):
    plot_type = st.selectbox(
        "Select plot type", ["Amplitude vs. BFR", "Frequency vs. BFR", "Duration vs. BFR"], index=0
    )
    if plot_type == "Amplitude vs. BFR":
        fig = px.scatter(
            data,
            x="strain_amplitude_µϵ",
            y="bone_formation_rate",
            color="frequency_Hz",
            labels={
                "strain_amplitude_µϵ": "Strain amplitude (µϵ)",
                "bone_formation_rate": "Bone formation rate (arb. units)",
                "frequency_Hz": "Frequency (Hz)",
            },
            title="Effect of strain amplitude on predicted bone formation rate",
        )
        st.plotly_chart(fig, use_container_width=True)
    elif plot_type == "Frequency vs. BFR":
        fig = px.scatter(
            data,
            x="frequency_Hz",
            y="bone_formation_rate",
            color="strain_amplitude_µϵ",
            labels={
                "frequency_Hz": "Frequency (Hz)",
                "bone_formation_rate": "Bone formation rate (arb. units)",
                "strain_amplitude_µϵ": "Strain amplitude (µϵ)",
            },
            title="Effect of loading frequency on predicted bone formation rate",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:  # Duration vs. BFR
        fig = px.scatter(
            data,
            x="duration_weeks",
            y="bone_formation_rate",
            color="strain_amplitude_µϵ",
            labels={
                "duration_weeks": "Duration (weeks)",
                "bone_formation_rate": "Bone formation rate (arb. units)",
                "strain_amplitude_µϵ": "Strain amplitude (µϵ)",
            },
            title="Effect of duration on predicted bone formation rate",
        )
        st.plotly_chart(fig, use_container_width=True)

# Additional information section
with st.expander("Background & References"):
        st.markdown(
        """
        ### Background

        Bone is a dynamic tissue that remodels in response to its mechanical
        environment. Experiments funded by the U.S. Public Health Service have
        shown that increasing the frequency and magnitude of cyclic mechanical
        loading can stimulate new bone formation【787350952497089†L305-L323】.  There is a
        lower mechanical threshold around 1050 µϵ (~40 N in rats) below which
        lamellar bone formation is not triggered【80783935968031†L300-L315】.  As strains
        approach an optimal range (~1500 µϵ), the anabolic response peaks,
        but very high strains can induce microdamage and modelling‑dependent bone
        loss【246402821972818†L107-L115】.  Repeated loading at supra‑physiological
        intensities or high accelerations may also cause fatigue damage to
        fragile bones【988135435614641†L186-L261】.  Similarly, frequencies much higher
        than those used in animal studies can desensitise osteocytes and reduce
        the anabolic response【245124096181909†L1194-L1204】.  Continuous long
        loading sessions can lead to desensitisation of osteocyte mechanosensors;
        dividing loading into multiple smaller bouts with rest periods yields
        more bone formation【766476793748597†L136-L145】.  Consequently, the
        anabolic effect of loading duration reaches a plateau and further
        extending the duration offers diminishing returns for bone formation【465350937148328†L260-L265】.

        The synthetic model used in this dashboard captures these trends: strains
        below the threshold produce only baseline bone formation; amplitudes
        between the threshold and the optimum (~1500 µϵ) and moderate frequencies
        (~5 Hz) produce the greatest increases; at higher strains or frequencies
        the predicted effect declines due to microdamage and reduced
        mechanosensitivity.  Duration also influences the response, but bones
        lose mechanosensitivity during continuous loading; beyond an optimal
        duration the anabolic effect saturates, so increasing the duration
        provides diminishing returns【766476793748597†L136-L145】【465350937148328†L260-L265】.

        ### Data Sources

        * **NASA Open Science Data Repository (OSD‑310):** A public dataset
          describing bone histomorphometry in rats flown in space.  The study
          found that cancellous bone loss during spaceflight was associated with
          increased bone resorption and marrow adiposity but no change in bone
          formation【640128976070130†L90-L115】.
        * **Frequency effects on bone formation:** Rat studies using cyclic
          compression at 1–10 Hz demonstrated that periosteal bone formation
          increases with both peak load and frequency【787350952497089†L305-L323】.
        * **Mechanical thresholds:** Strains above ~1050 µϵ are required to
          stimulate lamellar bone formation【80783935968031†L300-L315】, while strains
          beyond ~1500 µϵ can induce modelling‑dependent bone loss【246402821972818†L107-L115】.
          High‑intensity vibrations deliver repeated large accelerations and
          may endanger fragile bones or other tissues【988135435614641†L186-L261】.
        * **Frequency dependence and mechanosensitivity:** Increasing loading
          frequency reduces the microstrain required to trigger periosteal bone
          formation but very high frequencies can decrease the anabolic response
          due to diminished cell mechanosensitivity【245124096181909†L1194-L1204】.

        These resources are maintained by U.S. government agencies and
        peer‑reviewed journals and are publicly accessible.  Because the
        original data files are not directly consumable here, the dashboard
        uses a synthetic data set derived from the reported trends.
        """
    )