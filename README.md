# Effect Size Calculator

A powerful and intuitive desktop GUI application for calculating and visualizing a variety of statistical effect sizes. Built in Python using PyQt6, this tool guides users through loading datasets, selecting analysis types, and producing both numerical results and publication‑quality plots with ease.

## 🖼 Screenshots

A quick look at the app in both light and dark mode:

**Light Mode**\

<img width="532" height="721" alt="v3 3 Light Mode Screenshot " src="https://github.com/user-attachments/assets/aed0c7e1-f080-4c19-8d20-785ffd705cd5" />

**Dark Mode**\

<img width="536" height="719" alt="v3 3 Dark Mode Screenshot " src="https://github.com/user-attachments/assets/4421b4f7-4392-4b59-a13a-f511cd6b7e3e" />

---

## Key Features

- **Multiple Effect Size Metrics**
  - Categorical vs. Categorical: Cramér’s V with contingency‑table heatmaps or bar charts
  - Categorical vs. Numerical: Cohen’s d or η² (ANOVA) with box, violin, or strip plots
  - Numerical Correlation: Pearson’s r with scatter, regression, or hexbin plots
- **Flexible Data Input**
  - Load data from CSV or Excel (`.xlsx`) files
  - Preview the first 10 rows directly in the GUI table
- **Interactive Visualization**
  - Dark/light theme toggle for presentation‑ready styling
  - Customize plot type, axis labels, and add regression lines for scatterplots
  - Export charts as PNG, JPG, or PDF with a click
- **Real‑Time Validation & Progress**
  - Stepwise UI enables controls only when prerequisites are met (file loaded, previewed)
  - Progress bar indicates file loading and computation status
- **User‑Friendly Interface**
  - Clean layout with grouped sections: File & Columns, Data Preview, Analysis Settings, Results
  - Tooltips and error dialogs help prevent invalid inputs and guide analysis
- **Cross‑Platform & Extendable**
  - Runs on Windows, macOS, and Linux (requires Python 3.7+)
  - Source code organized under `src/main.py` for easy customization and contributions

---

## Getting Started

### Prerequisites

- **Python 3.7+** installed on your system
- Required libraries (install via pip): PyQt6, pandas, numpy, scipy, pingouin, matplotlib, seaborn, openpyxl

### Install from Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/EffectSizeCalculator.git
   cd EffectSizeCalculator
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Launch the application**:
   ```bash
   python src/main.py
   ```

### Install via Windows Installer

1. Download `EffectSizeCalculator_Setup_v3.3.exe` from [Releases](https://github.com/yourusername/EffectSizeCalculator/releases)
2. Run the installer and follow prompts
3. Launch **Effect Size Calculator** from Start menu or desktop shortcut

---

## Quick Usage Guide

1. **Load Your Data**: Click **Browse** and select a CSV or Excel file.
2. **Select Columns**: Choose two distinct columns (categorical or numeric).
3. **Preview Data**: Click **Preview Data** to verify your dataset.
4. **Set Analysis Options**: Pick effect size type, significance level (α), and plot style.
5. **Calculate Effect Size**: Click **Calculate Effect Size**; view numeric result in the summary panel.
6. **Preview/Save Plot**: Use **Preview Plot** to open a new window, then **Save Plot** to export your chart.

---

## Project Structure

```
EffectSizeCalculator/
├── .gitignore         # Exclude build artifacts and caches
├── LICENSE            # MIT License
├── README.md          # Project overview and instructions
├── requirements.txt   # List of Python dependencies
└── src/
    └── main.py        # PyQt6 application entry point
```

---

## Roadmap

- Add auto detect column types for easier usage.
- Support Omega squared and nonparametric effect sizes
- Provide installers for macOS (`.dmg`) and Linux (`.AppImage`)

---

## License

This project is distributed under the MIT License © 2024 Hen Zrihen. See [LICENSE](LICENSE) for details.

