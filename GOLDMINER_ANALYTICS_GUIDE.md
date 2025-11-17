# GoldMiner Analytics Notebook Guide

## Overview

`GoldMiner_Analytics.ipynb` is a comprehensive Jupyter notebook that provides interactive financial analytics and visualizations for transaction data stored in Parquet format. It offers executives and analysts a powerful, offline-capable tool for understanding spending patterns, detecting anomalies, and making data-driven financial decisions.

## Features

### 📊 Summary Statistics
- Total transactions and spending
- Mean, median, and standard deviation of transactions
- Credit vs Debit card usage analysis
- Account type breakdown with spend ratios
- Anomaly detection summary

### 🎛️ Interactive Filters
The notebook includes dynamic filtering widgets for:
- **Date Range**: Select start and end dates
- **Categories**: Multi-select category filter
- **Account Type**: Filter by Credit/Debit cards
- **Urgency Level**: Filter by transaction urgency

All visualizations automatically update when filters are applied.

### 📈 Visualizations

#### 1. Monthly Spend Timeline
- Interactive line chart showing spending trends over time
- Identifies highest and lowest spending months
- Calculates average monthly spend

#### 2. Category Breakdown
- Pie chart showing spending distribution across categories
- Treemap visualization for hierarchical view
- Top 5 categories with percentages

#### 3. Top 10 Merchants
- Horizontal bar chart of merchants with highest total spend
- Transaction count and average transaction amount per merchant
- Color-coded by spend amount

#### 4. Urgency Level Distribution
- Dual visualization: pie chart for counts, bar chart for spend
- Breakdown of normal, low, high, and critical urgency transactions

#### 5. Anomaly Detection Timeline
- Scatter plot showing all transactions
- Red diamond markers highlighting anomalous transactions
- Detailed hover information for each transaction
- Top 5 anomalous transactions listed

#### 6. Account Type Comparison
- Grouped bar chart comparing Credit vs Debit spending by category
- Category preference analysis by account type

### 💾 Export Functionality
Export all visualizations as PNG files for:
- Executive presentations
- Financial reports
- Documentation purposes

Files are saved to the `exports/` directory.

## Installation

### Prerequisites
Ensure you have Python 3.8+ installed.

### Install Dependencies

```bash
pip install -r requirements.txt
```

The notebook requires:
- `jupyter>=1.0.0` - Jupyter notebook environment
- `ipywidgets>=8.0.0` - Interactive widgets
- `matplotlib>=3.5.0` - Static visualizations
- `plotly>=5.0.0` - Interactive visualizations
- `kaleido>=0.2.0` - Image export for Plotly
- `pandas>=2.0.0` - Data processing
- `numpy>=1.24.0` - Numerical operations
- `pyarrow>=14.0.1` - Parquet file support

## Data Requirements

### Input Format
The notebook expects transaction data in Parquet format at:
```
data/processed/transactions.parquet
```

### Required Columns
- `id`: Transaction identifier
- `date`: Transaction date (datetime)
- `payee`: Merchant/payee name
- `category`: Transaction category
- `amount`: Transaction amount (numeric)
- `account_type`: Credit or Debit
- `urgency`: Transaction urgency level
- `anomaly_flag`: Anomaly indicator (optional)

### Optional Columns
- `subcategory`: Transaction subcategory
- `normalized_merchant`: Normalized merchant name
- `currency`: Transaction currency
- `account_id`: Account identifier
- `interest_rate`: Interest rate (for credit cards)
- `tags`: Transaction tags
- `confidence`: Confidence level

## Usage

### Starting the Notebook

1. Navigate to the project directory:
```bash
cd goldminer
```

2. Start Jupyter Notebook:
```bash
jupyter notebook
```

3. Open `GoldMiner_Analytics.ipynb` in your browser

### Running the Analysis

#### Option 1: Run All Cells
- Click **Cell → Run All** to execute the entire notebook
- All visualizations will be generated sequentially

#### Option 2: Step-by-Step Execution
1. **Setup** (Cells 1-2): Import libraries and configure settings
2. **Load Data** (Cell 3): Load transaction data from Parquet file
3. **Summary Statistics** (Cell 4): View key financial metrics
4. **Apply Filters** (Cell 5): Use interactive widgets to filter data
5. **Visualizations** (Cells 6-11): Generate individual charts
6. **Export** (Cell 12): Save visualizations as PNG files

### Working with Filters

1. Use the date pickers to select a date range
2. Select one or more categories (hold Ctrl/Cmd for multiple selections)
3. Choose account types to include
4. Select urgency levels to filter by
5. Click "Apply Filters" to update the filtered dataset
6. Re-run visualization cells to see updated charts
7. Click "Reset Filters" to return to the full dataset

### Exporting Visualizations

Run the export cell (Cell 12) to generate PNG files:
- `monthly_timeline.png` - Monthly spending trends
- `category_breakdown.png` - Category distribution
- `top_merchants.png` - Top 10 merchants
- `urgency_distribution.png` - Urgency levels
- `anomaly_timeline.png` - Anomaly detection

Files are saved to the `exports/` directory.

## Offline Functionality

The notebook is designed to work **completely offline**:
- All data is loaded from local Parquet files
- No internet connection required
- All visualizations render locally in the browser
- Export functionality works without external services

## Customization

### Changing Data Source
Edit the data path in Cell 3:
```python
DATA_PATH = Path('path/to/your/transactions.parquet')
```

### Adjusting Visualizations
Modify Plotly chart configurations in visualization cells:
```python
fig.update_layout(
    title='Custom Title',
    height=600,
    template='plotly_white'
)
```

### Adding New Filters
Add custom filter widgets in Cell 5:
```python
custom_filter = widgets.SelectMultiple(
    options=['Option1', 'Option2'],
    value=['Option1'],
    description='Custom Filter:'
)
```

### Modifying Summary Statistics
Add or remove statistics in Cell 4:
```python
custom_metric = df['amount'].quantile(0.75)
print(f"75th Percentile: ${custom_metric:,.2f}")
```

## Troubleshooting

### Issue: "transactions.parquet not found"
**Solution**: Ensure your data file exists at `data/processed/transactions.parquet` or update the `DATA_PATH` variable.

### Issue: Filters not updating visualizations
**Solution**: After applying filters, re-run the visualization cells (Cells 6-11) to see updated charts.

### Issue: Export fails in headless environment
**Solution**: Image export requires a display server. Run in Jupyter Notebook or JupyterLab with a GUI.

### Issue: Widget interactions not working
**Solution**: Ensure `ipywidgets` is properly installed:
```bash
pip install ipywidgets
jupyter nbextension enable --py widgetsnbextension
```

### Issue: Large dataset performance
**Solution**: 
- Filter data by date range before running analysis
- Consider sampling large datasets for faster rendering
- Increase system memory allocation

## Best Practices

### For Executive Reviewers
1. Read markdown cells for context and interpretation
2. Use filters to focus on specific time periods or categories
3. Export visualizations for presentations
4. Pay attention to anomaly detection for unusual transactions

### For Analysts
1. Start with summary statistics to understand data characteristics
2. Apply filters systematically to isolate trends
3. Cross-reference multiple visualizations for comprehensive insights
4. Document findings in new markdown cells

### For Developers
1. Keep data pipeline updated to generate fresh Parquet files
2. Validate data quality before running analytics
3. Customize visualizations based on stakeholder needs
4. Add new analysis sections as needed

## Integration with GoldMiner Pipeline

The notebook integrates seamlessly with the GoldMiner ETL pipeline:

1. **Generate Data**: Use `ParquetExporter` to export transaction data
```python
from goldminer.etl import ParquetExporter
exporter = ParquetExporter()
exporter.export_to_parquet(transactions, 'data/processed/transactions.parquet')
```

2. **Run Analytics**: Open and run `GoldMiner_Analytics.ipynb`

3. **Export Results**: Use the export functionality to save visualizations

## Performance Considerations

- **Small Datasets** (<1,000 transactions): Near-instant rendering
- **Medium Datasets** (1,000-10,000 transactions): Fast rendering (~1-2 seconds per chart)
- **Large Datasets** (>10,000 transactions): May require 5-10 seconds per visualization

For very large datasets (>100,000 transactions), consider:
- Pre-filtering data before loading
- Using data sampling for exploration
- Running analysis on a subset of data

## Examples

### Example 1: Analyzing Q4 Spending
1. Set date range: October 1 - December 31
2. Click "Apply Filters"
3. Run visualization cells
4. Export charts for Q4 report

### Example 2: Credit Card Analysis
1. Select "Credit" in account type filter
2. Apply filters
3. Compare category breakdown between credit and debit
4. Identify top credit card merchants

### Example 3: Anomaly Investigation
1. Run anomaly timeline visualization
2. Click on red diamond markers to see transaction details
3. Filter by high urgency to see critical transactions
4. Export anomaly timeline for fraud review

## Support and Contribution

For issues, questions, or contributions:
- Repository: https://github.com/seifelsherbinyy/goldminer
- Issues: Use GitHub Issues for bug reports
- Pull Requests: Contributions welcome

## License

This notebook is part of the GoldMiner project and is available under the MIT License.

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Author**: Seif Elsherbiny
