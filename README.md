# DataPulse-Real-Time-Data-Quality-Intelligence
DataPulse is an interactive Python-Dash platform that streamlines multi-file uploads, intelligent header mapping, automated data-quality analysis, and real-time cleaning. It delivers visual diagnostics, guided transformations, and metadata-rich exports for fast, reliable scientific data preparation.

## 🏆 Awards & Recognition
**Winner – Bristol Myers Squibb (BMS) Data Science Challenge 2025**  
This project was awarded first place for its real-time data quality monitoring,
intelligent cleaning workflow, and innovative data visualization capabilities.

## 🌟 Key Features

### 🚀 Multi-File Upload
- Upload up to **5 CSV/XLS/XLSX/XLSM files** (200MB each)
- Automatic file type detection, validation, and template matching
- Real-time upload progress and file summaries

### 🧠 Intelligent Data Compilation
- Automatic header mapping (exact, case-insensitive, fuzzy matching)
- Duplicate detection and removal
- Standardization of categories and missing value placeholders
- Interactive UI for reviewing and adjusting mappings

### 🔍 Comprehensive Data Quality Analysis
- Missing value counts, percentages, and pattern detection
- Numeric/date type validation
- Format inconsistencies, decimal precision checks, text standardization
- Outlier detection using **Z-score** and **IQR** methods
- Typo discovery using similarity algorithms

### 🛠️ Interactive Cleaning Tools
- Imputation methods: mean, median, mode, custom
- Date parsing and numeric conversion
- Outlier removal or winsorization
- Duplicate handling with impact summaries
- Text cleanup (casing, whitespace, normalization)
- Full change-tracking with before/after samples

### 📊 Visualization Module
- Histograms, boxplots, bar charts, scatter plots, line charts
- Automatic chart suggestions based on data type inference
- Statistical overlays and interactive tooltips

### 📦 Export with Metadata
- Export cleaned data in **CSV/XLSX** format
- Includes:
  - Cleaning history
  - Column statistics
  - Before/after snapshots
  - Processing notes and timestamps
- Optional **ZIP export** with structured documentation
