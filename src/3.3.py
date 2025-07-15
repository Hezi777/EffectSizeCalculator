import sys
import pandas as pd
import numpy as np
import scipy.stats as stats
import pingouin as pg
import matplotlib.pyplot as plt
import seaborn as sns

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog,
    QMessageBox, QCheckBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QGroupBox, QDialog, QFormLayout, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPalette, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import openpyxl


#######################################
#    Separate Window for Plot Display
#######################################
class PlotWindow(QDialog):
    def __init__(self, figure, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot")
        self.setMinimumSize(800, 600)

        self.main_layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(figure)
        self.main_layout.addWidget(self.canvas)


#######################################
#       Effect Size Interpretations
#######################################
def interpret_effect_size(value, effect_type):
    interpretations = {
        "cohen's d": [
            (0.2, 'small effect size'),
            (0.5, 'medium effect size'),
            (0.8, 'large effect size'),
            (float('inf'), 'very large effect size')
        ],
        "eta squared": [
            (0.01, 'small effect size'),
            (0.06, 'medium effect size'),
            (0.14, 'large effect size'),
            (float('inf'), 'very large effect size')
        ],
        "pearson's r": [
            (0.1, 'negligible correlation'),
            (0.3, 'small correlation'),
            (0.5, 'medium correlation'),
            (0.7, 'large correlation'),
            (0.9, 'very large correlation'),
            (float('inf'), 'perfect correlation')
        ],
        "cramér's v": [
            (0.1, 'small effect size'),
            (0.3, 'medium effect size'),
            (0.5, 'large effect size'),
            (float('inf'), 'very large effect size')
        ],
    }
    for threshold, interpretation in interpretations[effect_type.lower()]:
        if abs(value) < threshold:
            return interpretation


#######################################
#              Plot Functions
#######################################
def show_cramers_v_plot(contingency_table, cat_col1, cat_col2, plot_type):
    fig, ax = plt.subplots(figsize=(8, 6))
    if plot_type == "Stacked Bar Chart":
        contingency_table.plot(kind='bar', stacked=True, ax=ax)
    elif plot_type == "Grouped Bar Chart":
        contingency_table.plot(kind='bar', ax=ax)
    elif plot_type == "Heatmap":
        sns.heatmap(contingency_table, annot=True, cmap='YlGnBu', ax=ax)

    ax.set_title(f"{cat_col1} vs {cat_col2}")
    ax.set_xlabel(cat_col1)
    ax.set_ylabel('Count' if plot_type != "Heatmap" else cat_col2)
    plt.tight_layout()
    return fig


def show_cohens_d_plot(df, cat_col, num_col, plot_type):
    fig, ax = plt.subplots(figsize=(8, 6))
    if plot_type == "Box Plot":
        df.boxplot(column=num_col, by=cat_col, ax=ax)
    elif plot_type == "Violin Plot":
        sns.violinplot(x=cat_col, y=num_col, data=df, ax=ax)
    elif plot_type == "Strip Plot":
        sns.stripplot(x=cat_col, y=num_col, data=df, ax=ax)
    ax.set_title(f"{plot_type} of {num_col} by {cat_col}")
    ax.set_xlabel(cat_col)
    ax.set_ylabel(num_col)
    plt.suptitle('')
    plt.tight_layout()
    return fig


def show_pearsons_r_plot(df, col1, col2, plot_type, add_regression=False):
    fig, ax = plt.subplots(figsize=(8, 6))
    if plot_type == "Scatter Plot":
        ax.scatter(df[col1], df[col2])
        if add_regression:
            sns.regplot(x=col1, y=col2, data=df, ax=ax, scatter=False, color='red')
    elif plot_type == "Hexbin Plot":
        ax.hexbin(df[col1], df[col2], gridsize=20, cmap='Blues')
    elif plot_type == "Regression Plot":
        sns.regplot(x=col1, y=col2, data=df, ax=ax)

    ax.set_title(f"{plot_type} of {col1} vs {col2}")
    ax.set_xlabel(col1)
    ax.set_ylabel(col2)
    plt.tight_layout()
    return fig


#######################################
#         Effect Size Functions
#######################################
def cat_on_cat_effect_size(df, cat_col1, cat_col2, alpha):
    contingency_table = pd.crosstab(df[cat_col1], df[cat_col2])
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
    n = contingency_table.values.sum()
    r, k = contingency_table.shape
    denom = min((k - 1), (r - 1)) if min((k - 1), (r - 1)) > 0 else 1

    phi2 = chi2 / n
    cramers_v = np.sqrt(phi2 / denom)

    if p_value <= alpha:
        interpretation = interpret_effect_size(cramers_v, "Cramér's V")
        result_text = f"Cramér's V: {cramers_v:.3f} ({interpretation}) (p = {p_value:.3f})"
    else:
        result_text = f"Effect size not statistically significant (p = {p_value:.3f}, alpha = {alpha})"

    return result_text, contingency_table, cat_col1, cat_col2


def cat_on_num_effect_size(df, cat_col, num_col, alpha):
    df = df.copy()
    df[num_col] = pd.to_numeric(df[num_col], errors='coerce')
    df = df.dropna(subset=[cat_col, num_col])

    num_categories = df[cat_col].nunique()
    if num_categories < 2:
        raise ValueError("Categorical column must have at least 2 categories for comparison.")

    if num_categories == 2:
        unique_vals = df[cat_col].unique()
        group1 = df[df[cat_col] == unique_vals[0]][num_col]
        group2 = df[df[cat_col] == unique_vals[1]][num_col]
        t_stat, p_value = stats.ttest_ind(group1, group2)
        pooled_std = np.sqrt((group1.var(ddof=1) + group2.var(ddof=1)) / 2)
        if pooled_std == 0:
            raise ValueError("Pooled standard deviation is zero; cannot compute Cohen's d.")
        cohen_d_value = (group1.mean() - group2.mean()) / pooled_std
        if p_value <= alpha:
            interpretation = interpret_effect_size(cohen_d_value, "Cohen's d")
            result_text = f"Cohen's d: {cohen_d_value:.3f} ({interpretation}) (p = {p_value:.3f})"
        else:
            result_text = f"Effect size not statistically significant (p = {p_value:.3f}, alpha = {alpha})"
    else:
        anova_results = pg.anova(dv=num_col, between=cat_col, data=df, detailed=True)
        p_value = anova_results['p-unc'][0]
        eta_squared_value = anova_results['np2'][0]
        if p_value <= alpha:
            interpretation = interpret_effect_size(eta_squared_value, "Eta Squared")
            result_text = f"η² (Eta Squared): {eta_squared_value:.3f} ({interpretation}) (p = {p_value:.3f})"
        else:
            result_text = f"Effect size not statistically significant (p = {p_value:.3f}, alpha = {alpha})"

    return result_text, df, cat_col, num_col


def correlation_effect_size(df, col1, col2, alpha):
    df = df.copy()
    df[col1] = pd.to_numeric(df[col1], errors='coerce')
    df[col2] = pd.to_numeric(df[col2], errors='coerce')
    df = df.dropna(subset=[col1, col2])

    if len(df) < 2:
        raise ValueError("Not enough valid numeric data for correlation.")

    r, p_value = stats.pearsonr(df[col1], df[col2])
    if p_value <= alpha:
        interpretation = interpret_effect_size(r, "Pearson's r")
        result_text = f"Pearson's r: {r:.3f} ({interpretation}) (p = {p_value:.3f})"
    else:
        result_text = f"Effect size not statistically significant (p = {p_value:.3f}, alpha = {alpha})"

    return result_text, df, col1, col2


#######################################
#        Main Application Window
#######################################
class EffectSizeCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Effect Size Calculator")
        self.setMinimumSize(500, 700)

        # Start in light mode
        self.dark_mode = False

        # Initialize controls disabled until steps are completed
        self.file_loaded = False
        self.data_previewed = False

        self.init_ui()

        # 1) Apply style immediately
        self.apply_modern_style()

        # 2) Re-apply after the window is fully created to fix the QComboBox palette on first startup:
        QTimer.singleShot(0, self.apply_modern_style)

    def init_ui(self):
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout with vertical spacing
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)

        # Title row
        title_layout = QHBoxLayout()
        self.title_label = QLabel("Effect Size Calculator")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: 700;")
        title_layout.addWidget(self.title_label)

        # Toggle button
        self.mode_toggle_button = QPushButton("Dark Mode 🌙")  # Start in light => show action to go dark
        self.mode_toggle_button.setFixedWidth(130)
        self.mode_toggle_button.clicked.connect(self.toggle_dark_mode)
        title_layout.addWidget(self.mode_toggle_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addLayout(title_layout)

        ###############################
        # File & Columns Section
        ###############################
        file_group = QGroupBox("File & Columns")
        file_group.setStyleSheet("QGroupBox::title { font-weight: bold; }")

        file_layout = QGridLayout()
        file_layout.setContentsMargins(10, 10, 10, 10)
        file_layout.setHorizontalSpacing(10)
        file_layout.setVerticalSpacing(8)

        # File row
        self.file_label = QLabel("File Path")
        self.file_path_entry = QLineEdit()
        self.file_path_entry.setDisabled(True)
        self.file_browse_button = QPushButton("Browse")
        self.file_browse_button.clicked.connect(self.load_file)

        file_layout.addWidget(self.file_label, 0, 0)
        file_layout.addWidget(self.file_path_entry, 0, 1, 1, 2)
        file_layout.addWidget(self.file_browse_button, 0, 3)

        # Columns row
        self.col1_label = QLabel("Column 1")
        self.col1_menu = QComboBox()
        self.col1_menu.setEnabled(False)

        self.col2_label = QLabel("Column 2")
        self.col2_menu = QComboBox()
        self.col2_menu.setEnabled(False)

        self.col1_menu.setFixedWidth(150)
        self.col2_menu.setFixedWidth(150)

        file_layout.addWidget(self.col1_label, 1, 0)
        file_layout.addWidget(self.col1_menu, 1, 1)
        file_layout.addWidget(self.col2_label, 1, 2)
        file_layout.addWidget(self.col2_menu, 1, 3)

        file_group.setLayout(file_layout)
        self.main_layout.addWidget(file_group)

        ###############################
        # Data Preview Section
        ###############################
        preview_group = QGroupBox("Data Preview")
        preview_group.setStyleSheet("QGroupBox::title { font-weight: bold; }")
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(10, 10, 10, 10)

        self.data_table = QTableWidget()
        preview_layout.addWidget(self.data_table)

        self.preview_button = QPushButton("Preview Data")
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self.preview_data)
        preview_layout.addWidget(self.preview_button)

        preview_group.setLayout(preview_layout)
        self.main_layout.addWidget(preview_group)

        ###############################
        # Analysis Settings Section
        ###############################
        analysis_group = QGroupBox("Analysis Settings")
        analysis_group.setStyleSheet("QGroupBox::title { font-weight: bold; }")
        analysis_layout = QFormLayout()
        analysis_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        analysis_layout.setContentsMargins(10, 10, 10, 10)

        # Effect Size Type
        self.effect_type_label = QLabel("Effect Size Type")
        self.effect_type_menu = QComboBox()
        self.effect_type_menu.addItems([
            "Categorical on Categorical",
            "Categorical on Numerical",
            "Numerical Correlation"
        ])
        self.effect_type_menu.currentTextChanged.connect(self.update_plot_options)
        self.effect_type_menu.setEnabled(False)
        analysis_layout.addRow(self.effect_type_label, self.effect_type_menu)

        # Significance level
        self.alpha_label = QLabel("Significance (α)")
        self.alpha_entry = QLineEdit("0.05")
        self.alpha_entry.setEnabled(False)
        analysis_layout.addRow(self.alpha_label, self.alpha_entry)

        # Plot type
        self.plot_type_label = QLabel("Plot Type")
        self.plot_type_menu = QComboBox()
        self.plot_type_menu.setEnabled(False)
        analysis_layout.addRow(self.plot_type_label, self.plot_type_menu)

        # Regression checkbox
        self.regression_checkbox = QCheckBox("Add Regression Line (Scatter Plot)")
        self.regression_checkbox.setVisible(False)
        self.regression_checkbox.stateChanged.connect(self.update_plot)
        self.regression_checkbox.setEnabled(False)
        analysis_layout.addRow(self.regression_checkbox)

        analysis_group.setLayout(analysis_layout)
        self.main_layout.addWidget(analysis_group)

        ###############################
        # Buttons Row (Actions)
        ###############################
        buttons_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Calculate Effect Size")
        self.calculate_button.clicked.connect(self.calculate_effect_size)
        self.calculate_button.setEnabled(False)

        self.plot_button = QPushButton("Preview Plot")
        self.plot_button.clicked.connect(self.show_plot)
        self.plot_button.setEnabled(False)

        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(self.save_plot)
        self.save_button.setEnabled(False)

        buttons_layout.addWidget(self.calculate_button)
        buttons_layout.addWidget(self.plot_button)
        buttons_layout.addWidget(self.save_button)
        self.main_layout.addLayout(buttons_layout)

        ###############################
        # Progress Bar + Label
        ###############################
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_label = QLabel("")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        self.main_layout.addLayout(progress_layout)

        ###############################
        # Effect Size Result Section
        ###############################
        result_group = QGroupBox("Effect Size Result")
        result_group.setStyleSheet("QGroupBox::title { font-weight: bold; }")
        rg_layout = QVBoxLayout()
        rg_layout.setContentsMargins(10, 10, 10, 10)
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        rg_layout.addWidget(self.result_label)
        result_group.setLayout(rg_layout)
        self.main_layout.addWidget(result_group)

        self.update_plot_options()

    def apply_modern_style(self):
        """
        Applies either a pastel light or a darker theme to most widgets.
        Also sets a QPalette on each QComboBox so its text/background
        matches the chosen theme from the start.
        """
        if self.dark_mode:
            # Dark style
            dark_stylesheet = """
            * {
                font-family: "Segoe UI", sans-serif;
                font-size: 11pt;
            }
            QMainWindow {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #f0f0f0;
                font-weight: 600;
            }
            QLineEdit, QTableWidget, QGroupBox, QTextEdit {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #888;
                border-radius: 8px;
                padding: 6px;
            }
            QPushButton {
                background-color: #000000;
                color: #ffffff;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1c1c1c;
            }
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
            }
            QGroupBox {
                border: 1px solid #888;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #444;
                color: #ffffff;
                border: none;
            }
            """
            self.setStyleSheet(dark_stylesheet)
            self.mode_toggle_button.setText("Light Mode ☀️")

            # Manually set a dark palette for QComboBox
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Base, QColor("#3b3b3b"))
            dark_palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
            dark_palette.setColor(QPalette.ColorRole.Button, QColor("#3b3b3b"))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))

            self.col1_menu.setPalette(dark_palette)
            self.col2_menu.setPalette(dark_palette)
            self.effect_type_menu.setPalette(dark_palette)
            self.plot_type_menu.setPalette(dark_palette)

        else:
            # Light style
            light_stylesheet = """
            * {
                font-family: "Segoe UI", sans-serif;
                font-size: 11pt;
            }
            QMainWindow {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ECF4FE, stop:1 #FAFAFA
                );
            }
            QLabel {
                color: #333333;
                font-weight: 600;
            }
            QLineEdit, QTableWidget, QGroupBox, QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 6px;
            }
            QPushButton {
                background-color: #22177A;
                color: #ffffff;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #605EA1;
            }
            QCheckBox {
                color: #333333;
                font-weight: bold;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #f1f1f1;
                color: #333;
                border: none;
            }
            """
            self.setStyleSheet(light_stylesheet)
            self.mode_toggle_button.setText("Dark Mode 🌙")

            # Manually set a light palette for QComboBox
            light_palette = QPalette()
            light_palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            light_palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
            light_palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
            light_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))

            self.col1_menu.setPalette(light_palette)
            self.col2_menu.setPalette(light_palette)
            self.effect_type_menu.setPalette(light_palette)
            self.plot_type_menu.setPalette(light_palette)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_modern_style()

    ########################################
    #            File Loading
    ########################################
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        if file_path:
            self.file_path_entry.setText(file_path)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_label.setText("Loading file...")
            try:
                if file_path.endswith(".csv"):
                    self.df = pd.read_csv(file_path)
                else:
                    self.df = pd.read_excel(file_path, engine='openpyxl')

                self.progress_bar.setValue(100)
                self.progress_bar.setVisible(False)
                self.progress_label.setText("File loaded successfully!")
                self.file_loaded = True

                # Populate columns
                self.col1_menu.clear()
                self.col2_menu.clear()
                columns = [str(c) for c in self.df.columns]
                self.col1_menu.addItems(columns)
                self.col2_menu.addItems(columns)

                # Enable next step
                self.preview_button.setEnabled(True)
                self.col1_menu.setEnabled(True)
                self.col2_menu.setEnabled(True)
                self.effect_type_menu.setEnabled(True)
                self.alpha_entry.setEnabled(True)
                self.plot_type_menu.setEnabled(True)
                self.regression_checkbox.setEnabled(True)

            except Exception as e:
                self.progress_bar.setVisible(False)
                self.progress_label.setText("")
                QMessageBox.critical(self, "Error", f"Could not load file:\n{str(e)}")

    def preview_data(self):
        if not hasattr(self, 'df'):
            return
        self.data_table.clear()
        self.data_table.setRowCount(0)

        cols = list(self.df.columns)
        self.data_table.setColumnCount(len(cols))
        self.data_table.setHorizontalHeaderLabels([str(c) for c in cols])

        rows_to_show = min(10, len(self.df))
        self.data_table.setRowCount(rows_to_show)

        for i in range(rows_to_show):
            for j in range(len(cols)):
                val = self.df.iloc[i, j]
                self.data_table.setItem(i, j, QTableWidgetItem(str(val)))

        # Enable calculate button after preview
        self.data_previewed = True
        self.calculate_button.setEnabled(True)

    ########################################
    #       Plot Option Updates
    ########################################
    def update_plot_options(self):
        effect_type = self.effect_type_menu.currentText()
        self.plot_type_menu.clear()

        if effect_type == "Categorical on Categorical":
            self.plot_type_menu.addItems(["Stacked Bar Chart", "Grouped Bar Chart", "Heatmap"])
            self.regression_checkbox.setVisible(False)
        elif effect_type == "Categorical on Numerical":
            self.plot_type_menu.addItems(["Box Plot", "Violin Plot", "Strip Plot"])
            self.regression_checkbox.setVisible(False)
        elif effect_type == "Numerical Correlation":
            self.plot_type_menu.addItems(["Scatter Plot", "Hexbin Plot", "Regression Plot"])
            self.regression_checkbox.setVisible(True)

    def update_plot(self):
        if self.plot_button.isEnabled():
            self.show_plot()

    ########################################
    #       Calculate & Show Results
    ########################################
    def calculate_effect_size(self):
        if not hasattr(self, 'df'):
            QMessageBox.warning(self, "Warning", "Please load a dataset first.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Calculating...")

        try:
            alpha = float(self.alpha_entry.text())
        except ValueError:
            self.progress_bar.setVisible(False)
            self.progress_label.setText("")
            QMessageBox.critical(self, "Error", "Significance (α) must be a numeric value.")
            return

        effect_type = self.effect_type_menu.currentText()
        col1 = self.col1_menu.currentText()
        col2 = self.col2_menu.currentText()

        if col1 == col2:
            self.progress_bar.setVisible(False)
            self.progress_label.setText("")
            QMessageBox.critical(self, "Error", "Please select two different columns.")
            return

        try:
            if effect_type == "Categorical on Categorical":
                result_text, contingency_table, cat1, cat2 = cat_on_cat_effect_size(self.df, col1, col2, alpha)
            elif effect_type == "Categorical on Numerical":
                result_text, df_used, cat_col, num_col = cat_on_num_effect_size(self.df, col1, col2, alpha)
            else:
                result_text, df_used, c1, c2 = correlation_effect_size(self.df, col1, col2, alpha)

            self.result_label.setText(result_text)
            self.plot_data = (self.df, col1, col2, effect_type)
            self.plot_button.setEnabled(True)
            self.save_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Calculation complete.")

    ########################################
    #           Show / Save Plot
    ########################################
    def show_plot(self):
        if not hasattr(self, 'plot_data'):
            return

        df, col1, col2, effect_type = self.plot_data
        plot_type = self.plot_type_menu.currentText()

        try:
            if effect_type == "Categorical on Categorical":
                contingency_table = pd.crosstab(df[col1], df[col2])
                fig = show_cramers_v_plot(contingency_table, col1, col2, plot_type)
            elif effect_type == "Categorical on Numerical":
                fig = show_cohens_d_plot(df, col1, col2, plot_type)
            else:
                add_regression = self.regression_checkbox.isChecked()
                fig = show_pearsons_r_plot(df, col1, col2, plot_type, add_regression)

            # Show plot in a separate dialog
            plot_dialog = PlotWindow(fig, self)
            plot_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_plot(self):
        if not hasattr(self, 'plot_data'):
            return

        df, col1, col2, effect_type = self.plot_data
        plot_type = self.plot_type_menu.currentText()

        try:
            if effect_type == "Categorical on Categorical":
                contingency_table = pd.crosstab(df[col1], df[col2])
                fig = show_cramers_v_plot(contingency_table, col1, col2, plot_type)
            elif effect_type == "Categorical on Numerical":
                fig = show_cohens_d_plot(df, col1, col2, plot_type)
            else:
                add_regression = self.regression_checkbox.isChecked()
                fig = show_pearsons_r_plot(df, col1, col2, plot_type, add_regression)

            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save Plot", "",
                "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf)"
            )
            if file_name:
                fig.savefig(file_name)
                QMessageBox.information(self, "Saved", "Plot saved successfully!")
            plt.close(fig)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


#######################################
#                MAIN
#######################################
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = EffectSizeCalculator()
    window.show()

    sys.exit(app.exec())
