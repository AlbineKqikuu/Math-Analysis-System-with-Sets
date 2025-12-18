# Math Analysis System with Sets

A powerful Python-based tool for set theory operations, visualization, and code analysis. This system allows users to define multiple sets, perform complex operations using a visual expression builder, and generate detailed reports.

## 🚀 Features

- **Interactive Set Definition**: Define up to 4 sets (A, B, C, D) using intuitive text inputs.
- **Visual Expression Builder**: Easily build set operations using symbols:
  - `∪` Union
  - `∩` Intersection
  - `\` Set Difference
  - `Δ` Symmetric Difference
- **Venn Diagram Visualization**: Automatically generates Venn diagrams for 2 or 3 sets.
- **Membership Tables**: Generates detailed tables showing the relationship of elements across all sets.
- **Subset Detection**: Automatically detects and informs the user about subset relationships (e.g., A ⊆ B).
- **Multi-format Export**:
  - **TXT**: High-level summary and table.
  - **CSV**: Raw data for spreadsheet analysis.
  - **PDF**: Professional reports including a **Live Code Metrics** analysis section.
- **Code Metrics Analysis**: Integrated tools (Radon, Pylint) to analyze code complexity, maintainability, and quality directly from the GUI.

## 🛠️ Installation

Ensure you have Python installed, then install the required dependencies:

```bash
pip install matplotlib matplotlib-venn reportlab radon pylint
```

## 💻 How to Run

Simply run the primary script:

```bash
python main3.py
```

## 📄 License
This project is for educational purposes. Feel free to use and modify!
