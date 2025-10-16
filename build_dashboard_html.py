"""
Script to build a standalone HTML dashboard for the mechanobiology project.

The generated HTML file (`mechanobiology_dashboard.html`) contains:

1. An interactive input panel where users can specify mechanical loading
   parameters (frequency, strain amplitude and duration) and select a bone
   region.  A JavaScript function computes the predicted bone formation rate
   using the same synthetic model implemented in Python.  This allows the
   prediction to run entirely in the browser without any backend.

2. Three Plotly figures showing the relationships between strain amplitude,
   frequency, duration and bone formation rate across a synthetic dataset.
   The Plotly library is embedded directly into the HTML so that no external
   downloads are required.

3. A table summarising the synthetic dataset and a section describing the
   underlying science with citations.  These citations refer to the lines in
   the PubMed and NASA sources included in the final report【787350952497089†L305-L323】【80783935968031†L300-L315】【640128976070130†L90-L115】.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio

# NOTE: The functions `generate_synthetic_dataset` and
# `predict_bone_formation_rate` are redefined here to avoid importing the
# Streamlit‑based dashboard module.  Streamlit is not available in this
# environment, so these standalone definitions reproduce the same
# functionality without external dependencies.

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

    See `mechanobiology_dashboard.generate_synthetic_dataset` for details.  This
    function is duplicated here to avoid importing Streamlit.
    """
    rng = np.random.default_rng(seed=42)
    freq = rng.uniform(freq_range[0], freq_range[1], n_samples)
    amplitude = rng.uniform(amplitude_range[0], amplitude_range[1], n_samples)
    duration = rng.uniform(time_range[0], time_range[1], n_samples)
    # Inverted U shape for amplitude response
    amp_effect = np.zeros_like(amplitude)
    rising = (amplitude > threshold) & (amplitude <= optimum_amplitude)
    amp_effect[rising] = (amplitude[rising] - threshold) / (optimum_amplitude - threshold)
    falling = amplitude > optimum_amplitude
    amp_effect[falling] = np.maximum((max_amplitude - amplitude[falling]) / (max_amplitude - optimum_amplitude), 0.0)

    # Triangular frequency response peaking at mid‑point of freq_range
    freq_effect = np.zeros_like(freq)
    freq_min, freq_max = freq_range
    freq_opt = (freq_min + freq_max) / 2.0
    low = (freq >= freq_min) & (freq <= freq_opt)
    freq_effect[low] = (freq[low] - freq_min) / (freq_opt - freq_min)
    high = freq > freq_opt
    freq_effect[high] = np.maximum((freq_max - freq[high]) / (freq_max - freq_opt), 0.0)

    # Duration effect saturates beyond an optimum; continuous loading reduces
    # mechanosensitivity【766476793748597†L136-L145】.  Normalize by
    # optimum_duration and cap at 1.
    duration_effect = np.minimum(duration / optimum_duration, 1.0)
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

    See `mechanobiology_dashboard.predict_bone_formation_rate` for details.
    """
    # amplitude response
    if amplitude <= threshold:
        amp_effect = 0.0
    elif amplitude <= optimum_amplitude:
        amp_effect = (amplitude - threshold) / (optimum_amplitude - threshold)
    else:
        amp_effect = max((max_amplitude - amplitude) / (max_amplitude - optimum_amplitude), 0.0)

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

    # Duration saturates beyond optimum; prolonged continuous sessions provide
    # diminishing returns【766476793748597†L136-L145】.  Cap at 1.
    duration_effect = min(duration / optimum_duration, 1.0)
    return baseline_bfr + max_increase * amp_effect * freq_effect * duration_effect

def build_dashboard_html(output_path: str = "mechanobiology_dashboard.html") -> None:
    """Generate the dashboard HTML file.

    Parameters
    ----------
    output_path : str
        Path where the HTML file will be written.
    """
    # Create synthetic data
    data = generate_synthetic_dataset(n_samples=300)

    # Round numeric values for readability in the table
    table_data = data.round(
        {
            "frequency_Hz": 2,
            "strain_amplitude_µϵ": 0,
            "duration_weeks": 2,
            "bone_formation_rate": 2,
        }
    ).to_dict(orient="records")

    # Convert dataset to JSON for embedding in JavaScript
    dataset_json = json.dumps(table_data)

    # Generate Plotly figures
    fig_amp = px.scatter(
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

    fig_freq = px.scatter(
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

    fig_duration = px.scatter(
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

    # Convert figures to HTML; include PlotlyJS only in the first figure
    fig_amp_html = pio.to_html(
        fig_amp, include_plotlyjs=True, full_html=False, config={"responsive": True}
    )
    fig_freq_html = pio.to_html(
        fig_freq, include_plotlyjs=False, full_html=False, config={"responsive": True}
    )
    fig_duration_html = pio.to_html(
        fig_duration, include_plotlyjs=False, full_html=False, config={"responsive": True}
    )

    # HTML template
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Mechanobiology Data Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
        header {{ background-color: #272727; color: #fff; padding: 1rem; text-align: center; }}
        main {{ padding: 1rem 2rem; }}
        .container {{ display: flex; flex-wrap: wrap; gap: 2rem; }}
        .input-panel {{ flex: 1 1 300px; background-color: #f5f5f5; padding: 1rem; border-radius: 8px; }}
        .output-panel {{ flex: 2 1 600px; }}
        label {{ display: block; margin-top: 0.5rem; }}
        input, select {{ width: 100%; padding: 0.4rem; margin-top: 0.2rem; }}
        button {{ margin-top: 0.8rem; padding: 0.5rem 1rem; background-color: #007BFF; color: #fff; border: none; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background-color: #0056b3; }}
        #prediction-result {{ margin-top: 1rem; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; overflow-x: auto; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
        th {{ background-color: #f2f2f2; }}
        .references {{ margin-top: 2rem; font-size: 0.9rem; color: #555; }}
        .references a {{ color: #007BFF; text-decoration: none; }}
        .references a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <h1>Mechanobiology Data Dashboard</h1>
        <p>Explore how mechanical loading parameters influence bone formation rate</p>
    </header>
    <main>
        <div class="container">
            <div class="input-panel">
                <h2>Input parameters</h2>
                <label for="region">Bone region</label>
                <select id="region">
                    <option value="Tibia">Tibia</option>
                    <option value="Ulna">Ulna</option>
                    <option value="Vertebra">Vertebra</option>
                    <option value="Femur">Femur</option>
                    <option value="Humerus">Humerus</option>
                </select>
                <label for="frequency">Loading frequency (Hz)</label>
                <input type="number" id="frequency" min="1" max="10" step="0.5" value="5" />
                <label for="amplitude">Strain amplitude (µϵ)</label>
                <input type="number" id="amplitude" min="0" max="3000" step="50" value="1500" />
                <label for="duration">Duration (weeks)</label>
                <input type="number" id="duration" min="1" max="8" step="0.5" value="2" />
                <button id="predict-btn" type="button">Predict bone formation rate</button>
                <div id="prediction-result"></div>
            </div>
            <div class="output-panel">
                <h2>Synthetic data visualisation</h2>
                <!-- Plotly figures -->
                <div id="fig-amp">{fig_amp_html}</div>
                <div id="fig-freq" style="margin-top: 2rem;">{fig_freq_html}</div>
                <div id="fig-duration" style="margin-top: 2rem;">{fig_duration_html}</div>
            </div>
        </div>
        <h2>Synthetic data table</h2>
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Frequency (Hz)</th>
                        <th>Amplitude (µϵ)</th>
                        <th>Duration (weeks)</th>
                        <th>Bone formation rate</th>
                    </tr>
                </thead>
                <tbody id="data-table-body"></tbody>
            </table>
        </div>
        <div class="references">
            <h3>Background &amp; references</h3>
            <p>
                Research funded by the U.S. Public Health Service shows that bone
                formation increases with loading frequency and magnitude; higher
                frequencies and peak loads stimulate more periosteal bone
                formation【787350952497089†L305-L323】.  There is a lower threshold
                around 1050 µϵ (~40 N in rat tibia) below which lamellar bone
                formation is not triggered【80783935968031†L300-L315】.  As strain
                amplitude increases toward an optimal range (~1500 µϵ), the
                anabolic response peaks; very high strains can induce
                microdamage and modelling‑dependent bone loss【246402821972818†L107-L115】.
                Repeated high‑intensity vibrations deliver large accelerations and
                may produce fatigue damage in fragile bones and other tissues【988135435614641†L186-L261】.
                Continuous long loading sessions can desensitise the bone’s
                mechanosensors; breaking loading into multiple smaller bouts
                with recovery periods yields greater bone mass【766476793748597†L136-L145】.
                Consequently, the anabolic effect of loading duration reaches a
                plateau and further extending the duration provides diminishing
                returns【465350937148328†L260-L265】.
                The synthetic model in this dashboard therefore assumes an
                inverted‑U response to strain amplitude and a bell‑shaped
                response to frequency, with the strongest stimulation around
                5 Hz【245124096181909†L1194-L1204】.
                NASA's open data set OSD‑310 reports that spaceflight causes
                cancellous bone loss accompanied by increased bone resorption but
                no change in bone formation【640128976070130†L90-L115】.  Because the
                original data files are not directly consumable here, the
                synthetic dataset and prediction model were derived from these
                public findings.
            </p>
        </div>
    </main>
    <script>
        // Embedded synthetic dataset for table rendering
        const dataset = {dataset_json};

        // Function to populate the data table
        function populateTable() {{
            const tbody = document.getElementById('data-table-body');
            dataset.forEach(row => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${{row.frequency_Hz.toFixed(2)}}</td>
                    <td>${{Math.round(row.strain_amplitude_µϵ)}}</td>
                    <td>${{row.duration_weeks.toFixed(2)}}</td>
                    <td>${{row.bone_formation_rate.toFixed(2)}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        // Call table population on page load
        populateTable();

        // Attach event listener for prediction button to avoid inline onclick handlers
        document.getElementById('predict-btn').addEventListener('click', predictBFR);

        // Prediction model (same formula as Python but implemented in JavaScript)
        function predictBFR() {{
            // Read user inputs
            const freq = parseFloat(document.getElementById('frequency').value);
            const amp = parseFloat(document.getElementById('amplitude').value);
            const dur = parseFloat(document.getElementById('duration').value);

            // Parameters defining the mechanostat response
            const threshold = 1050.0;        // below this, lamellar formation is not triggered
            const optAmp = 1500.0;           // optimum strain amplitude (~1500 µϵ)
            const maxAmp = 3000.0;           // maximum amplitude considered; response declines toward this
            const baseline = 1.0;            // baseline bone formation rate
            const maxIncrease = 5.0;         // maximum multiplicative increase above baseline
            const freqMin = 1.0;             // minimum frequency in synthetic dataset
            const freqMax = 10.0;            // maximum frequency
            const freqOpt = 5.0;             // optimum frequency (~5 Hz)

            // Compute amplitude effect as an inverted U shape
            let ampEffect;
            if (amp <= threshold) {{
                ampEffect = 0.0;
            }} else if (amp <= optAmp) {{
                ampEffect = (amp - threshold) / (optAmp - threshold);
            }} else {{
                ampEffect = Math.max((maxAmp - amp) / (maxAmp - optAmp), 0.0);
            }}

            // Compute frequency effect as a triangular response peaking at freqOpt
            let freqEffect;
            if (freq <= freqMin) {{
                freqEffect = 0.0;
            }} else if (freq <= freqOpt) {{
                freqEffect = (freq - freqMin) / (freqOpt - freqMin);
            }} else if (freq <= freqMax) {{
                freqEffect = Math.max((freqMax - freq) / (freqMax - freqOpt), 0.0);
            }} else {{
                freqEffect = 0.0;
            }}

            // Duration effect saturates beyond an optimum duration.  Continuous
            // loading leads to desensitisation; we normalise by the optimum
            // duration (3 weeks) and cap the effect at 1.0【766476793748597†L136-L145】【465350937148328†L260-L265】.
            const optDur = 3.0;
            const durEffect = Math.min(dur / optDur, 1.0);

            // Predict bone formation rate
            const bfr = baseline + maxIncrease * ampEffect * freqEffect * durEffect;

            // Provide qualitative interpretation based on thresholds
            let interpretation;
            if (amp <= threshold) {{
                interpretation = "The strain amplitude is below the ~1050 µϵ threshold, so only baseline bone formation is expected.";
            }} else if (amp > optAmp) {{
                interpretation = "The strain amplitude exceeds the optimal ~1500 µϵ range; high strains may cause microdamage and modelling‑dependent bone loss.";
            }} else if (freq > freqOpt) {{
                interpretation = "The loading frequency is above the optimum range; mechanosensitivity may decrease at high frequencies, reducing the anabolic response.";
            }} else if (dur > optDur) {{
                interpretation = "Long loading durations do not indefinitely increase bone formation. Continuous sessions can desensitise bone mechanosensors; splitting loading into shorter bouts with rest is more effective. Beyond ~3 weeks the anabolic effect saturates, so extending duration adds little benefit.";
            }} else {{
                interpretation = "Parameters are in the optimal range for stimulating bone formation.";
            }}

            // Display result and interpretation
            document.getElementById('prediction-result').innerHTML =
                `<p>Predicted bone formation rate: <strong>${{bfr.toFixed(2)}}</strong> (arbitrary units).</p>` +
                `<p>${{interpretation}}</p>`;
        }}
    </script>
</body>
</html>
"""

    # Write HTML file
    Path(output_path).write_text(html_template, encoding="utf-8")


if __name__ == "__main__":
    build_dashboard_html()