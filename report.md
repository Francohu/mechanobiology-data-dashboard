# Mechanobiology Data Dashboard (Updated Version)

## Project Background and Scientific Basis

Bone is a typical mechanosensitive tissue whose formation and remodeling are regulated by mechanical strain and vibration frequency. Many U.S. government–funded studies have released relevant open data, providing the foundation for constructing this interactive model.

* **Strain Threshold and Damage** – Frost’s *mechanostat theory* defines different bone responses to strain: strains below approximately 100 µε lead to bone resorption; 100–1500 µε stimulate bone formation; strains above ~1500 µε induce microdamage and modeling-dependent bone loss. This indicates an optimal strain range, beyond which excessive loading harms bone.
* **Microdamage and Fatigue Loading** – A *PLOS One* study found that repeated fatigue loading on human vertebrae accumulates microcracks in trabeculae, significantly reducing Young’s modulus and mechanical strength. This demonstrates that long-term or high-amplitude cyclic stress can damage bone and diminish osteogenic potential.
* **Risks of High-Intensity Vibration** – A review by *Melioguide* noted that some commercial whole-body vibration platforms operate at up to 90 Hz and 0.05–3 mm amplitude, producing peak accelerations potentially dangerous to fragile bones and cartilage. Amplitudes above 0.5 mm (~1500 µε) may cause fatigue damage to the musculoskeletal system; researchers recommend avoiding such intensities.
* **Frequency-Dependent Mechanosensitivity** – *Frontiers* reviews show that cellular mechanosensitivity decreases with increasing frequency; at high frequencies, stronger strain is required to produce the same osteogenic response, while excessive frequency reduces bone adaptation due to increased cellular stiffness.
* **Frequency and Threshold Effects** – NIH animal experiments indicate that within 1–10 Hz cyclic compression, bone formation increases with peak load in a dose-dependent manner, but strain below ~1050 µε produces minimal effect.

These findings show that the mechanical stimulus–bone response follows an inverted-U curve: low strain fails to trigger bone formation; moderate strain and frequency stimulate bone adaptation; excessive strain or vibration frequency causes microdamage or desensitization, inhibiting osteogenesis.  
This project synthesizes mechanobiological trends from U.S. open data (NIH, NASA) to generate a representative dataset for modeling and visualization.

---

## Synthetic Data and Predictive Model

Since original NASA GeneLab OSD-310 datasets are stored in binary formats not easily parsed, this project simulates ~300 experimental conditions based on literature trends.  
Each sample includes loading frequency, strain amplitude, and duration, and predicts a **bone formation rate (BFR)** using the following model principles.

### 1. Triangular Amplitude Effect

* **Threshold:** Strain below ~1050 µε → baseline bone formation  
* **Optimum:** ~1500 µε → maximal osteogenic response per Frost’s mechanostat  
* **Upper Limit:** >3000 µε (~0.5 mm amplitude vibration) → microdamage and inhibition

**Amplitude effect (inverted-U):**

- `amp ≤ threshold` → `amp_effect = 0` (baseline)  
- `threshold < amp ≤ opt_amp` → `amp_effect = (amp - threshold)/(opt_amp - threshold)`  
- `opt_amp < amp ≤ max_amp` → `amp_effect = (max_amp - amp)/(max_amp - opt_amp)`  
- `amp > max_amp` → `amp_effect = 0` (damage)

---

### 2. Frequency Effect

* **Range:** 1–10 Hz, following NIH studies.  
* **Optimum:** ~5 Hz yields peak mechanosensitivity.

Triangular function:
- 1→5 Hz: linear increase in `freq_effect`  
- 5→10 Hz: linear decrease due to mechanoreceptor desensitization.

---

### 3. Duration Effect

Duration (1–4 weeks) contributes linearly: longer exposure yields higher cumulative bone formation.  
Animal studies show osteogenic effects after ~1–2 weeks; thus each week adds 0.5 relative units.

---

### 4. Predictive Formula

\[
\mathrm{BFR} = 1 + 5 \times \mathrm{amp\_effect} \times \mathrm{freq\_effect} \times \frac{\mathrm{duration}}{2}.
\]

When both strain and frequency are optimal,  
`amp_effect × freq_effect = 1`, yielding the highest BFR.  
Excessive or insufficient mechanical inputs reduce BFR to baseline, modeling both activation thresholds and overloading damage.

---

## Web Application Features

The website (static front-end) runs locally on any modern browser and demonstrates the full “data → model → interaction” process.

| Function | Description |
|-----------|--------------|
| **Parameter Input & Prediction** | Select a bone region (e.g., tibia, femur), input loading frequency, strain amplitude, and duration, then click *Predict bone formation rate*. The app outputs predicted BFR and safety messages if inputs fall below threshold or exceed safe strain limits. |
| **Synthetic Data Visualization** | Interactive scatterplots show strain vs. BFR (colored by frequency), frequency vs. BFR (colored by strain), and duration vs. BFR. Plots highlight the inverted-U relationships. |
| **Data Table** | A full table of 300 simulated loading cases and BFR predictions allows detailed inspection. |
| **Scientific References** | Footer includes citations from U.S. government and journal sources for context. |

---

## Usage and Customization

1. **Local Use:** Download and open the HTML file directly — no server required.  
2. **Model Editing:** In Python (Streamlit version), users can adjust strain/frequency thresholds or load real data.  
3. **Data Replacement:** Once NASA/NIH datasets are available in readable format, they can replace the synthetic data for validation or machine-learning optimization.

---

## Future Extensions

* **Regional Variation:** Different bones may have distinct mechanosensitivities.  
* **Additional Biological Factors:** Incorporate load direction, fluid shear, and rest intervals.  
* **Safety Module:** Add warnings when vibration amplitude exceeds safe physiological levels for rehabilitation or sports applications.

---

## Summary

This project integrates open mechanobiology data from U.S. agencies (NIH, NASA) and published literature to build a demonstration-level **Mechanobiology Data Dashboard**.  
The model captures the dual effect of mechanical stimulation—moderate loads promote bone formation while excessive loads or frequencies suppress it through microdamage or desensitization.  
Through its interactive visualizations, this project illustrates the complete process of deriving quantitative rules from open data, building predictive models, and presenting them through accessible web tools.  
It serves as both a research showcase and an educational resource in biomedical engineering, demonstrating how open data can be transformed into interactive, reproducible science.
