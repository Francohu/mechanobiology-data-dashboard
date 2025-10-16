# Mechanobiology Data Dashboard

An interactive dashboard for exploring how mechanical loading parameters influence bone formation rate.  This project illustrates how to convert mechanobiology data into an interactive model for research demonstrations and interviews.  The application is provided as both a Streamlit web app (Python) and a self‑contained static HTML page.

## Features

- **Input parameters:** Choose a bone region and enter mechanical loading frequency (Hz), strain amplitude (µε) and duration (weeks).  The model predicts a dimensionless bone formation rate.
- **Triangular and inverted‑U responses:**  
  * Strain amplitude has a minimum threshold (~1050 µε) below which no bone forms and an optimal range around 1500 µε.  Beyond ~1500 µε, bone formation declines because high strains cause microdamage and modeling‑dependent bone loss【246402821972818†L107-L115】.  
  * Loading frequency shows a triangular response peaking around 5 Hz; very high frequencies reduce mechanosensitivity【245124096181909†L1194-L1204】.  
  * Loading duration exhibits diminishing returns: prolonged continuous loading desensitises bone mechano‑receptors and increases risk of fatigue damage【766476793748597†L136-L145】; the model caps the effect after ~3 weeks.
- **Synthetic data visualisation:** The dashboard displays scatter plots showing how bone formation rate varies with strain amplitude and frequency over a synthetic dataset.  Colour gradients visualise frequency or amplitude.
- **Interpretive messages:** Output messages alert when inputs fall below thresholds, exceed optimal ranges, or risk microdamage/high‑frequency fatigue.
- **Cross‑platform:**  
  * `mechanobiology_dashboard.py` – a Streamlit app that can be run locally (`streamlit run mechanobiology_dashboard.py`).  
  * `mechanobiology_dashboard.html` – a static web page that runs in any modern browser without a Python backend.  
  * `build_dashboard_html.py` – generates the static HTML from the Python source and synthetic data.
- **Comprehensive report:** See `report.md` for a deep dive into the science behind the model and references to NASA, NIH and other open data sources.

## Repository Contents

| File | Description |
| --- | --- |
| `mechanobiology_dashboard.py` | Streamlit application for interactive exploration and prediction. |
| `mechanobiology_dashboard.html` | Self‑contained static version of the dashboard. |
| `build_dashboard_html.py` | Script that generates the static HTML dashboard from the Python code and synthesised data. |
| `report.md` | Detailed report explaining the model, data sources, citations and future improvements. |
| `README.md` | (This file) Project overview and usage instructions. |

## Usage

### Run the Streamlit app

```bash
# Install dependencies
pip install streamlit pandas plotly

# Launch the app
streamlit run mechanobiology_dashboard.py
```

The app will open in your default browser.  Enter loading parameters, click **Predict bone formation rate**, and explore the plots.

### Use the static HTML dashboard

Open `mechanobiology_dashboard.html` in any modern web browser.  All interactive functionality (including predictive logic and plots) is embedded without requiring a backend server.

### Rebuild the static HTML

If you modify the Streamlit app and wish to regenerate the static dashboard:

```bash
python build_dashboard_html.py
```

The script synthesises a dataset and embeds it along with JavaScript prediction logic into a new HTML file.

## Data sources

This dashboard was inspired by publicly available mechanobiology studies:

- **NASA OSD‑310 dataset:** Reports bone loss, bone marrow adiposity increase and changes in cancellous bone in mice during spaceflight【408128976070130†L90-L115】.
- **Frost’s mechanostat theory:** Describes ranges of strain (<100 µε bone resorption, ~100–1500 µε adaptive modelling, >1500 µε modelling‑dependent bone loss)【246402821972818†L107-L115】.
- **Fatigue loading microdamage study:** Cyclic high‑strain loading accumulates microcracks and reduces mechanical strength【869018023511247†L170-L195】.
- **Vibration therapy safety:** High‑intensity vibrations (>0.5 mm amplitude, >30 Hz) may cause fatigue damage and are not recommended【988135435614641†L186-L261】.
- **Loading duration and desensitisation:** Continuous loading can desensitise mechanoreceptors; intermittent sessions with rest periods are more effective【766476793748597†L136-L145】.

These sources informed the thresholds, optimal ranges and warnings implemented in the model.  See `report.md` for complete citations and discussion.

## License

This project is provided for educational and research purposes.  You may use, modify and distribute it at your own risk.  Cite the original data sources and this repository as appropriate.

## Citation
Hu, Qinfu (2025). *Mechanobiology Data Dashboard: Predicting Bone Formation Rate from Mechanical Loading Parameters.* Zenodo. https://doi.org/10.5281/zenodo.17365836

