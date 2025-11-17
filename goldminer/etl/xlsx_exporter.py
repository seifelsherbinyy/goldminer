"""
XLSX Exporter module for exporting transaction data to Excel workbooks.

This module provides the XLSXExporter class for creating well-formatted Excel workbooks
with multiple sheets, charts, and formatting suitable for non-technical users.
"""
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.chart import PieChart, BarChart, LineChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows
from goldminer.utils import setup_logger


class XLSXExporter:
    """
    Exports transaction data to well-formatted Excel workbooks.
    
    Creates multi-sheet workbooks with:
    - Transactions: Full row-level data
    - Monthly Summary: Aggregated totals by category/account
    - Anomalies: Records with anomaly flags
    
    Features:
    - Formatted headers with freeze panes
    - Auto-adjusted column widths
    - Currency formatting for amounts
    - Highlighted anomaly rows
    - Charts: pie (category share), bar (monthly spend), line (cumulative)
    - UTF-8 compatible
    """
    
    def __init__(self):
        """Initialize the XLSX exporter."""
        self.logger = setup_logger(__name__)
        
        # Define styling constants
        self.header_font = Font(bold=True, color="FFFFFF", size=11)
        self.header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.anomaly_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        self.header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        self.logger.info("XLSXExporter initialized")
    
    def export_to_excel(self, transactions: List[Dict[str, Any]], filename: str) -> None:
        """
        Export transactions to a well-formatted Excel workbook.
        
        Args:
            transactions: List of transaction dictionaries with keys like:
                - date, amount, payee, category, subcategory, account_id, 
                  account_type, anomalies, etc.
            filename: Output filename for the Excel workbook
            
        Raises:
            ValueError: If transactions list is empty or filename is invalid
            IOError: If unable to write to the specified file
        """
        if not transactions:
            raise ValueError("Cannot export empty transaction list")
        
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        self.logger.info(f"Exporting {len(transactions)} transactions to {filename}")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(transactions)
        
        # Create workbook
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # Create sheets
        self._create_transactions_sheet(wb, df)
        self._create_monthly_summary_sheet(wb, df)
        self._create_anomalies_sheet(wb, df)
        
        # Save workbook
        try:
            wb.save(filename)
            self.logger.info(f"Successfully exported to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save workbook: {e}")
            raise IOError(f"Unable to write to file {filename}: {e}")
    
    def _create_transactions_sheet(self, wb: Workbook, df: pd.DataFrame) -> None:
        """
        Create the Transactions sheet with full row-level data.
        
        Args:
            wb: Workbook object
            df: DataFrame with transaction data
        """
        ws = wb.create_sheet("Transactions", 0)
        
        # Define column order and headers
        columns = [
            'id', 'date', 'payee', 'category', 'subcategory', 
            'amount', 'currency', 'account_id', 'account_type',
            'tags', 'anomalies', 'confidence'
        ]
        
        # Filter columns that exist in the dataframe
        available_columns = [col for col in columns if col in df.columns]
        df_subset = df[available_columns].copy()
        
        # Write data to sheet
        for r_idx, row in enumerate(dataframe_to_rows(df_subset, index=False, header=True), 1):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)
                
                # Style header row
                if r_idx == 1:
                    cell.font = self.header_font
                    cell.fill = self.header_fill
                    cell.alignment = self.header_alignment
                    cell.border = self.border
                else:
                    cell.border = self.border
                    
                    # Apply currency formatting to amount column
                    if available_columns[c_idx - 1] == 'amount' and value is not None:
                        cell.number_format = numbers.FORMAT_CURRENCY_USD_SIMPLE
                    
                    # Highlight anomaly rows
                    if 'anomalies' in available_columns:
                        anomaly_col_idx = available_columns.index('anomalies') + 1
                        anomaly_value = ws.cell(row=r_idx, column=anomaly_col_idx).value
                        if anomaly_value and str(anomaly_value).strip():
                            cell.fill = self.anomaly_fill
        
        # Freeze top row
        ws.freeze_panes = ws['A2']
        
        # Auto-adjust column widths
        self._auto_adjust_column_widths(ws)
        
        self.logger.info(f"Created Transactions sheet with {len(df)} rows")
    
    def _create_monthly_summary_sheet(self, wb: Workbook, df: pd.DataFrame) -> None:
        """
        Create the Monthly Summary sheet with aggregated totals.
        
        Args:
            wb: Workbook object
            df: DataFrame with transaction data
        """
        ws = wb.create_sheet("Monthly Summary", 1)
        
        # Ensure date column exists and is properly formatted
        if 'date' not in df.columns or 'amount' not in df.columns:
            self.logger.warning("Missing required columns for monthly summary")
            return
        
        # Convert date to datetime if it's not already
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
        df_copy = df_copy.dropna(subset=['date'])
        
        if df_copy.empty:
            self.logger.warning("No valid dates found for monthly summary")
            return
        
        # Extract year-month
        df_copy['year_month'] = df_copy['date'].dt.to_period('M').astype(str)
        
        # Create summary by month and category
        summary_data = []
        
        # Overall monthly totals
        monthly_totals = df_copy.groupby('year_month')['amount'].agg(['sum', 'mean', 'count']).reset_index()
        monthly_totals.columns = ['Month', 'Total', 'Average', 'Count']
        
        # Category breakdown
        if 'category' in df_copy.columns:
            category_summary = df_copy.groupby(['year_month', 'category'])['amount'].sum().reset_index()
            category_pivot = category_summary.pivot(index='year_month', columns='category', values='amount').fillna(0)
        
        # Account breakdown
        if 'account_id' in df_copy.columns:
            account_summary = df_copy.groupby(['year_month', 'account_id'])['amount'].sum().reset_index()
        
        # Write monthly totals section
        ws['A1'] = 'Monthly Transaction Summary'
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:D1')
        
        # Write headers and data for monthly totals
        row_idx = 3
        for r_idx, row in enumerate(dataframe_to_rows(monthly_totals, index=False, header=True), row_idx):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)
                if r_idx == row_idx:  # Header row
                    cell.font = self.header_font
                    cell.fill = self.header_fill
                    cell.alignment = self.header_alignment
                else:
                    if c_idx in [2, 3]:  # Total and Average columns
                        cell.number_format = numbers.FORMAT_CURRENCY_USD_SIMPLE
        
        # Write category breakdown if available
        if 'category' in df_copy.columns:
            row_idx = len(monthly_totals) + 6
            ws.cell(row=row_idx, column=1, value='Spending by Category')
            ws.cell(row=row_idx, column=1).font = Font(bold=True, size=12)
            
            row_idx += 2
            category_pivot_reset = category_pivot.reset_index()
            for r_idx, row in enumerate(dataframe_to_rows(category_pivot_reset, index=False, header=True), row_idx):
                for c_idx, value in enumerate(row, 1):
                    cell = ws.cell(row=r_idx, column=c_idx, value=value)
                    if r_idx == row_idx:  # Header row
                        cell.font = self.header_font
                        cell.fill = self.header_fill
                        cell.alignment = self.header_alignment
                    elif c_idx > 1:  # Amount columns
                        cell.number_format = numbers.FORMAT_CURRENCY_USD_SIMPLE
        
        # Freeze top rows
        ws.freeze_panes = ws['A4']
        
        # Auto-adjust column widths
        self._auto_adjust_column_widths(ws)
        
        # Add charts
        self._add_charts(ws, monthly_totals, df_copy)
        
        self.logger.info("Created Monthly Summary sheet")
    
    def _create_anomalies_sheet(self, wb: Workbook, df: pd.DataFrame) -> None:
        """
        Create the Anomalies sheet with flagged transactions only.
        
        Args:
            wb: Workbook object
            df: DataFrame with transaction data
        """
        ws = wb.create_sheet("Anomalies", 2)
        
        # Filter transactions with anomalies
        if 'anomalies' not in df.columns:
            ws['A1'] = 'No anomaly data available'
            self.logger.warning("No anomalies column found")
            return
        
        # Filter for rows with non-empty anomalies
        df_anomalies = df[df['anomalies'].notna() & (df['anomalies'] != '')].copy()
        
        if df_anomalies.empty:
            ws['A1'] = 'No anomalies detected'
            self.logger.info("No anomalies found")
            return
        
        # Define columns to show
        columns = [
            'id', 'date', 'payee', 'category', 'amount', 
            'account_id', 'anomalies', 'confidence'
        ]
        available_columns = [col for col in columns if col in df_anomalies.columns]
        df_subset = df_anomalies[available_columns].copy()
        
        # Write data to sheet
        for r_idx, row in enumerate(dataframe_to_rows(df_subset, index=False, header=True), 1):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)
                
                # Style header row
                if r_idx == 1:
                    cell.font = self.header_font
                    cell.fill = self.header_fill
                    cell.alignment = self.header_alignment
                    cell.border = self.border
                else:
                    cell.border = self.border
                    cell.fill = self.anomaly_fill  # Highlight all anomaly rows
                    
                    # Apply currency formatting to amount column
                    if available_columns[c_idx - 1] == 'amount' and value is not None:
                        cell.number_format = numbers.FORMAT_CURRENCY_USD_SIMPLE
        
        # Freeze top row
        ws.freeze_panes = ws['A2']
        
        # Auto-adjust column widths
        self._auto_adjust_column_widths(ws)
        
        self.logger.info(f"Created Anomalies sheet with {len(df_anomalies)} rows")
    
    def _add_charts(self, ws, monthly_totals: pd.DataFrame, df: pd.DataFrame) -> None:
        """
        Add charts to the Monthly Summary sheet.
        
        Args:
            ws: Worksheet object
            monthly_totals: DataFrame with monthly summary data
            df: Original DataFrame with transaction data
        """
        if monthly_totals.empty:
            return
        
        # Calculate chart positions (to the right of the data)
        chart_col_start = 10
        
        # 1. Pie Chart - Category Share
        if 'category' in df.columns:
            category_totals = df.groupby('category')['amount'].sum().reset_index()
            
            # Write category data for chart
            chart_data_row = 3
            ws.cell(row=chart_data_row, column=chart_col_start, value='Category')
            ws.cell(row=chart_data_row, column=chart_col_start + 1, value='Total')
            for idx, row in enumerate(category_totals.itertuples(), chart_data_row + 1):
                ws.cell(row=idx, column=chart_col_start, value=row.category)
                ws.cell(row=idx, column=chart_col_start + 1, value=row.amount)
            
            # Create pie chart
            pie = PieChart()
            pie.title = "Spending by Category"
            pie.style = 10
            pie.width = 15
            pie.height = 10
            
            # Add data to chart
            data = Reference(ws, min_col=chart_col_start + 1, min_row=chart_data_row, 
                           max_row=chart_data_row + len(category_totals))
            cats = Reference(ws, min_col=chart_col_start, min_row=chart_data_row + 1, 
                           max_row=chart_data_row + len(category_totals))
            pie.add_data(data, titles_from_data=True)
            pie.set_categories(cats)
            
            ws.add_chart(pie, f"J3")
        
        # 2. Bar Chart - Monthly Spend
        bar = BarChart()
        bar.type = "col"
        bar.title = "Monthly Spending"
        bar.y_axis.title = 'Amount'
        bar.x_axis.title = 'Month'
        bar.width = 15
        bar.height = 10
        
        data_rows = len(monthly_totals) + 3
        data = Reference(ws, min_col=2, min_row=3, max_row=data_rows, max_col=2)
        cats = Reference(ws, min_col=1, min_row=4, max_row=data_rows)
        bar.add_data(data, titles_from_data=True)
        bar.set_categories(cats)
        
        ws.add_chart(bar, "J20")
        
        # 3. Line Chart - Cumulative Spending
        line = LineChart()
        line.title = "Cumulative Spending Trend"
        line.y_axis.title = 'Cumulative Amount'
        line.x_axis.title = 'Month'
        line.width = 15
        line.height = 10
        
        # Calculate cumulative sum
        cumulative_col = 5
        ws.cell(row=3, column=cumulative_col, value='Cumulative')
        cumulative_sum = 0
        for idx, row in enumerate(monthly_totals.itertuples(), 4):
            cumulative_sum += row.Total
            ws.cell(row=idx, column=cumulative_col, value=cumulative_sum)
        
        data = Reference(ws, min_col=cumulative_col, min_row=3, max_row=data_rows)
        cats = Reference(ws, min_col=1, min_row=4, max_row=data_rows)
        line.add_data(data, titles_from_data=True)
        line.set_categories(cats)
        
        ws.add_chart(line, "J37")
        
        self.logger.info("Added charts to Monthly Summary sheet")
    
    def _auto_adjust_column_widths(self, ws) -> None:
        """
        Auto-adjust column widths based on content.
        
        Args:
            ws: Worksheet object
        """
        from openpyxl.cell.cell import MergedCell
        
        for column in ws.columns:
            max_length = 0
            column_letter = None
            
            for cell in column:
                # Skip merged cells
                if isinstance(cell, MergedCell):
                    continue
                    
                if column_letter is None:
                    column_letter = cell.column_letter
                
                try:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except:
                    pass
            
            # Only adjust if we found a valid column letter
            if column_letter:
                # Set width with some padding, but cap at reasonable maximum
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = max(adjusted_width, 10)
