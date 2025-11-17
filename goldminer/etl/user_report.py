"""
User Report Generation module for creating polished Excel workbooks.

This module provides the generate_user_report function that creates comprehensive
Excel workbooks with transactions, anomalies, summary sheets, and embedded charts
using xlsxwriter for enhanced visualization capabilities.
"""
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
import xlsxwriter
from goldminer.utils import setup_logger


def generate_user_report(transactions: List[dict], output_path: str) -> None:
    """
    Generate a polished Excel user report with transactions, anomalies, and summary sheets.
    
    Creates a comprehensive .xlsx workbook containing:
    - Transactions: All parsed rows with tagged metadata
    - Anomalies: Red-highlighted rows for quick review
    - Summary: Pivoted monthly category totals with embedded charts
    
    Charts include:
    - Monthly spend line chart
    - Category breakdown pie chart
    - Merchant bar chart (top 5)
    
    All sheets have consistent column formats, bold headers, filters, and readable styling.
    
    Args:
        transactions: List of transaction dictionaries with keys like:
            - date, amount, payee, category, subcategory, account_id,
              account_type, anomalies, tags, etc.
        output_path: Output filename for the Excel workbook (will add .xlsx if missing)
        
    Raises:
        ValueError: If transactions list is empty or output_path is invalid
        IOError: If unable to write to the specified file
        
    Example:
        >>> transactions = [
        ...     {'date': '2024-01-01', 'amount': 100.0, 'payee': 'Store',
        ...      'category': 'Food', 'anomalies': ''},
        ...     # ... more transactions
        ... ]
        >>> generate_user_report(transactions, 'financial_report.xlsx')
    """
    logger = setup_logger(__name__)
    
    if not transactions:
        raise ValueError("Cannot generate report from empty transaction list")
    
    # Ensure .xlsx extension
    if not output_path.endswith('.xlsx'):
        output_path += '.xlsx'
    
    logger.info(f"Generating user report for {len(transactions)} transactions to {output_path}")
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(transactions)
    
    # Create workbook with xlsxwriter
    try:
        workbook = xlsxwriter.Workbook(output_path, {'nan_inf_to_errors': True})
        
        # Define common formats
        formats = _create_formats(workbook)
        
        # Create sheets
        _create_transactions_sheet(workbook, df, formats, logger)
        _create_anomalies_sheet(workbook, df, formats, logger)
        _create_summary_sheet(workbook, df, formats, logger)
        
        # Close workbook
        workbook.close()
        logger.info(f"Successfully generated user report: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate user report: {e}")
        raise IOError(f"Unable to write to file {output_path}: {e}")


def _create_formats(workbook: xlsxwriter.Workbook) -> Dict[str, Any]:
    """
    Create reusable cell formats for consistent styling.
    
    Args:
        workbook: xlsxwriter Workbook object
        
    Returns:
        Dictionary of format objects
    """
    formats = {
        'header': workbook.add_format({
            'bold': True,
            'bg_color': '#366092',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        }),
        'currency': workbook.add_format({
            'num_format': '$#,##0.00',
            'border': 1
        }),
        'date': workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'border': 1
        }),
        'text': workbook.add_format({
            'border': 1
        }),
        'anomaly': workbook.add_format({
            'bg_color': '#FFC7CE',
            'border': 1
        }),
        'anomaly_currency': workbook.add_format({
            'num_format': '$#,##0.00',
            'bg_color': '#FFC7CE',
            'border': 1
        }),
        'anomaly_date': workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'bg_color': '#FFC7CE',
            'border': 1
        }),
        'title': workbook.add_format({
            'bold': True,
            'font_size': 14
        }),
        'subtitle': workbook.add_format({
            'bold': True,
            'font_size': 12
        })
    }
    return formats


def _create_transactions_sheet(workbook: xlsxwriter.Workbook, df: pd.DataFrame, 
                               formats: Dict[str, Any], logger) -> None:
    """
    Create the Transactions sheet with all parsed rows and tagged metadata.
    
    Args:
        workbook: xlsxwriter Workbook object
        df: DataFrame with transaction data
        formats: Dictionary of cell formats
        logger: Logger instance
    """
    worksheet = workbook.add_worksheet('Transactions')
    
    # Define column order and headers
    columns = [
        'id', 'date', 'payee', 'category', 'subcategory',
        'amount', 'currency', 'account_id', 'account_type',
        'tags', 'anomalies', 'confidence'
    ]
    
    # Filter columns that exist in the dataframe
    available_columns = [col for col in columns if col in df.columns]
    df_subset = df[available_columns].copy()
    
    # Write headers
    for col_idx, col_name in enumerate(available_columns):
        worksheet.write(0, col_idx, col_name, formats['header'])
    
    # Write data rows
    for row_idx, row in df_subset.iterrows():
        has_anomaly = 'anomalies' in available_columns and row.get('anomalies') and str(row.get('anomalies')).strip()
        
        for col_idx, col_name in enumerate(available_columns):
            value = row[col_name]
            
            # Select appropriate format based on column type and anomaly status
            if has_anomaly:
                if col_name == 'amount':
                    cell_format = formats['anomaly_currency']
                elif col_name == 'date':
                    cell_format = formats['anomaly_date']
                else:
                    cell_format = formats['anomaly']
            else:
                if col_name == 'amount':
                    cell_format = formats['currency']
                elif col_name == 'date':
                    cell_format = formats['date']
                else:
                    cell_format = formats['text']
            
            worksheet.write(row_idx + 1, col_idx, value, cell_format)
    
    # Set column widths
    column_widths = {
        'id': 12,
        'date': 12,
        'payee': 25,
        'category': 18,
        'subcategory': 18,
        'amount': 12,
        'currency': 10,
        'account_id': 15,
        'account_type': 12,
        'tags': 15,
        'anomalies': 20,
        'confidence': 12
    }
    
    for col_idx, col_name in enumerate(available_columns):
        width = column_widths.get(col_name, 15)
        worksheet.set_column(col_idx, col_idx, width)
    
    # Freeze top row
    worksheet.freeze_panes(1, 0)
    
    # Add autofilter
    if len(df_subset) > 0:
        worksheet.autofilter(0, 0, len(df_subset), len(available_columns) - 1)
    
    logger.info(f"Created Transactions sheet with {len(df_subset)} rows")


def _create_anomalies_sheet(workbook: xlsxwriter.Workbook, df: pd.DataFrame,
                            formats: Dict[str, Any], logger) -> None:
    """
    Create the Anomalies sheet with red-highlighted rows for quick review.
    
    Args:
        workbook: xlsxwriter Workbook object
        df: DataFrame with transaction data
        formats: Dictionary of cell formats
        logger: Logger instance
    """
    worksheet = workbook.add_worksheet('Anomalies')
    
    # Filter transactions with anomalies
    if 'anomalies' not in df.columns:
        worksheet.write(0, 0, 'No anomaly data available', formats['text'])
        logger.warning("No anomalies column found")
        return
    
    # Filter for rows with non-empty anomalies
    df_anomalies = df[df['anomalies'].notna() & (df['anomalies'] != '')].copy()
    
    if df_anomalies.empty:
        worksheet.write(0, 0, 'No anomalies detected', formats['text'])
        logger.info("No anomalies found")
        return
    
    # Define columns to show
    columns = [
        'id', 'date', 'payee', 'category', 'amount',
        'account_id', 'anomalies', 'confidence'
    ]
    available_columns = [col for col in columns if col in df_anomalies.columns]
    df_subset = df_anomalies[available_columns].copy()
    
    # Write headers
    for col_idx, col_name in enumerate(available_columns):
        worksheet.write(0, col_idx, col_name, formats['header'])
    
    # Write data rows (all with anomaly highlighting)
    for row_idx, row in df_subset.iterrows():
        for col_idx, col_name in enumerate(available_columns):
            value = row[col_name]
            
            # All rows are anomalies, so use anomaly formats
            if col_name == 'amount':
                cell_format = formats['anomaly_currency']
            elif col_name == 'date':
                cell_format = formats['anomaly_date']
            else:
                cell_format = formats['anomaly']
            
            worksheet.write(row_idx - df_subset.index[0] + 1, col_idx, value, cell_format)
    
    # Set column widths
    column_widths = {
        'id': 12,
        'date': 12,
        'payee': 25,
        'category': 18,
        'amount': 12,
        'account_id': 15,
        'anomalies': 20,
        'confidence': 12
    }
    
    for col_idx, col_name in enumerate(available_columns):
        width = column_widths.get(col_name, 15)
        worksheet.set_column(col_idx, col_idx, width)
    
    # Freeze top row
    worksheet.freeze_panes(1, 0)
    
    # Add autofilter
    if len(df_subset) > 0:
        worksheet.autofilter(0, 0, len(df_subset), len(available_columns) - 1)
    
    logger.info(f"Created Anomalies sheet with {len(df_subset)} rows")


def _create_summary_sheet(workbook: xlsxwriter.Workbook, df: pd.DataFrame,
                         formats: Dict[str, Any], logger) -> None:
    """
    Create the Summary sheet with pivoted monthly category totals and embedded charts.
    
    Includes:
    - Monthly spend line chart
    - Category breakdown pie chart
    - Merchant bar chart (top 5)
    
    Args:
        workbook: xlsxwriter Workbook object
        df: DataFrame with transaction data
        formats: Dictionary of cell formats
        logger: Logger instance
    """
    worksheet = workbook.add_worksheet('Summary')
    
    # Ensure required columns exist
    if 'date' not in df.columns or 'amount' not in df.columns:
        worksheet.write(0, 0, 'Missing required columns for summary', formats['text'])
        logger.warning("Missing required columns for summary")
        return
    
    # Convert date to datetime and extract year-month
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
    df_copy = df_copy.dropna(subset=['date'])
    
    if df_copy.empty:
        worksheet.write(0, 0, 'No valid dates found for summary', formats['text'])
        logger.warning("No valid dates found for summary")
        return
    
    df_copy['year_month'] = df_copy['date'].dt.to_period('M').astype(str)
    
    # Write title
    worksheet.write(0, 0, 'Financial Summary Report', formats['title'])
    
    row = 2
    
    # 1. Monthly Totals Section
    worksheet.write(row, 0, 'Monthly Transaction Summary', formats['subtitle'])
    row += 1
    
    monthly_totals = df_copy.groupby('year_month')['amount'].agg(['sum', 'mean', 'count']).reset_index()
    monthly_totals.columns = ['Month', 'Total', 'Average', 'Count']
    
    # Write monthly totals
    headers = ['Month', 'Total', 'Average', 'Count']
    for col_idx, header in enumerate(headers):
        worksheet.write(row, col_idx, header, formats['header'])
    
    row += 1
    monthly_start_row = row
    
    for _, month_row in monthly_totals.iterrows():
        worksheet.write(row, 0, month_row['Month'], formats['text'])
        worksheet.write(row, 1, month_row['Total'], formats['currency'])
        worksheet.write(row, 2, month_row['Average'], formats['currency'])
        worksheet.write(row, 3, month_row['Count'], formats['text'])
        row += 1
    
    monthly_end_row = row - 1
    
    # 2. Category Breakdown Section
    row += 2
    worksheet.write(row, 0, 'Spending by Category', formats['subtitle'])
    row += 1
    
    if 'category' in df_copy.columns:
        category_summary = df_copy.groupby(['year_month', 'category'])['amount'].sum().reset_index()
        category_pivot = category_summary.pivot(index='year_month', columns='category', values='amount').fillna(0)
        
        # Write category pivot table
        worksheet.write(row, 0, 'Month', formats['header'])
        for col_idx, category in enumerate(category_pivot.columns, 1):
            worksheet.write(row, col_idx, category, formats['header'])
        
        row += 1
        category_start_row = row
        
        for month, month_data in category_pivot.iterrows():
            worksheet.write(row, 0, str(month), formats['text'])
            for col_idx, value in enumerate(month_data, 1):
                worksheet.write(row, col_idx, value, formats['currency'])
            row += 1
        
        category_end_row = row - 1
    
    # 3. Top Merchants Section
    row += 2
    worksheet.write(row, 0, 'Top 5 Merchants by Spending', formats['subtitle'])
    row += 1
    
    if 'payee' in df_copy.columns:
        merchant_totals = df_copy.groupby('payee')['amount'].sum().sort_values(ascending=False).head(5)
        
        worksheet.write(row, 0, 'Merchant', formats['header'])
        worksheet.write(row, 1, 'Total Spending', formats['header'])
        
        row += 1
        merchant_start_row = row
        
        for merchant, total in merchant_totals.items():
            worksheet.write(row, 0, merchant, formats['text'])
            worksheet.write(row, 1, total, formats['currency'])
            row += 1
        
        merchant_end_row = row - 1
    
    # Add charts with dynamic sizing and styling
    chart_row = 2
    chart_col = 6
    
    # Extract year range for dynamic titles
    min_year = df_copy['date'].dt.year.min()
    max_year = df_copy['date'].dt.year.max()
    year_range = f"{min_year}" if min_year == max_year else f"{min_year}–{max_year}"
    
    # 1. Monthly Spend Line Chart
    if len(monthly_totals) > 0:
        line_chart = workbook.add_chart({'type': 'line'})
        line_chart.add_series({
            'name': 'Monthly Spending',
            'categories': ['Summary', monthly_start_row, 0, monthly_end_row, 0],
            'values': ['Summary', monthly_start_row, 1, monthly_end_row, 1],
            'line': {'color': '#4472C4', 'width': 2.5}
        })
        
        # Dynamic title with year
        line_chart.set_title({'name': f'Monthly Spend – {year_range}'})
        line_chart.set_x_axis({'name': 'Month', 'num_font': {'size': 9}})
        line_chart.set_y_axis({'name': 'Amount ($)', 'num_format': '$#,##0'})
        
        # Auto-size based on number of months (min 300, max 500 height)
        num_months = len(monthly_totals)
        chart_height = min(500, max(300, 200 + num_months * 15))
        line_chart.set_size({'width': 500, 'height': chart_height})
        line_chart.set_style(10)
        
        worksheet.insert_chart(chart_row, chart_col, line_chart)
        chart_row += int(chart_height / 15) + 2  # Dynamic spacing based on chart height
    
    # 2. Category Breakdown Pie Chart
    if 'category' in df_copy.columns:
        category_totals = df_copy.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        # Write data for pie chart in a separate area
        pie_data_col = 10
        pie_data_row = 2
        worksheet.write(pie_data_row, pie_data_col, 'Category', formats['header'])
        worksheet.write(pie_data_row, pie_data_col + 1, 'Total', formats['header'])
        
        pie_start_row = pie_data_row + 1
        for idx, (category, total) in enumerate(category_totals.items()):
            worksheet.write(pie_start_row + idx, pie_data_col, category, formats['text'])
            worksheet.write(pie_start_row + idx, pie_data_col + 1, total, formats['currency'])
        pie_end_row = pie_start_row + len(category_totals) - 1
        
        # Excel theme color palette for pie slices
        theme_colors = [
            '#4472C4',  # Blue
            '#ED7D31',  # Orange
            '#A5A5A5',  # Gray
            '#FFC000',  # Yellow
            '#5B9BD5',  # Light Blue
            '#70AD47',  # Green
            '#264478',  # Dark Blue
            '#9E480E',  # Dark Orange
            '#636363',  # Dark Gray
            '#997300'   # Dark Yellow
        ]
        
        pie_chart = workbook.add_chart({'type': 'pie'})
        pie_chart.add_series({
            'name': 'Category Breakdown',
            'categories': ['Summary', pie_start_row, pie_data_col, pie_end_row, pie_data_col],
            'values': ['Summary', pie_start_row, pie_data_col + 1, pie_end_row, pie_data_col + 1],
            'data_labels': {'percentage': True, 'font': {'size': 9}},
            'points': [
                {'fill': {'color': theme_colors[i % len(theme_colors)]}}
                for i in range(len(category_totals))
            ]
        })
        
        # Dynamic title with year
        pie_chart.set_title({'name': f'Category-Wise Expense Share – {year_range}'})
        
        # Auto-size based on number of categories (min 300, max 450 height)
        num_categories = len(category_totals)
        chart_height = min(450, max(300, 250 + num_categories * 10))
        pie_chart.set_size({'width': 500, 'height': chart_height})
        pie_chart.set_style(10)
        
        worksheet.insert_chart(chart_row, chart_col, pie_chart)
        chart_row += int(chart_height / 15) + 2  # Dynamic spacing
    
    # 3. Merchant Bar Chart (Top 5)
    if 'payee' in df_copy.columns and merchant_end_row >= merchant_start_row:
        # Excel theme color gradient for bars
        bar_colors = ['#4472C4', '#5B9BD5', '#70AD47', '#FFC000', '#ED7D31']
        
        bar_chart = workbook.add_chart({'type': 'bar'})
        bar_chart.add_series({
            'name': 'Spending',
            'categories': ['Summary', merchant_start_row, 0, merchant_end_row, 0],
            'values': ['Summary', merchant_start_row, 1, merchant_end_row, 1],
            'fill': {'color': '#4472C4'},
            'points': [
                {'fill': {'color': bar_colors[i % len(bar_colors)]}}
                for i in range(min(5, merchant_end_row - merchant_start_row + 1))
            ]
        })
        
        # Dynamic title with year
        bar_chart.set_title({'name': f'Top 5 Merchants by Volume – {year_range}'})
        bar_chart.set_x_axis({'name': 'Amount ($)', 'num_format': '$#,##0', 'num_font': {'size': 9}})
        bar_chart.set_y_axis({'name': 'Merchant', 'num_font': {'size': 9}})
        
        # Auto-size based on number of merchants (optimized for top 5)
        num_merchants = min(5, merchant_end_row - merchant_start_row + 1)
        chart_height = min(400, max(250, 150 + num_merchants * 40))
        bar_chart.set_size({'width': 500, 'height': chart_height})
        bar_chart.set_style(10)
        
        worksheet.insert_chart(chart_row, chart_col, bar_chart)
    
    # Set column widths
    worksheet.set_column(0, 0, 15)  # Month/Category column
    worksheet.set_column(1, 4, 12)  # Amount columns
    
    # Freeze top rows
    worksheet.freeze_panes(3, 0)
    
    logger.info("Created Summary sheet with charts")
