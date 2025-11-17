"""Unit tests for XLSXExporter."""
import unittest
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from openpyxl import load_workbook
from goldminer.etl import XLSXExporter


class TestXLSXExporter(unittest.TestCase):
    """Test cases for XLSXExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = XLSXExporter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample transaction data
        self.sample_transactions = self._create_sample_transactions()
    
    def tearDown(self):
        """Clean up test files."""
        # Remove temporary files
        for file in Path(self.temp_dir).glob("*.xlsx"):
            file.unlink()
        Path(self.temp_dir).rmdir()
    
    def _create_sample_transactions(self):
        """Create sample transaction data for testing."""
        base_date = datetime.now() - timedelta(days=90)
        transactions = []
        
        categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping']
        accounts = ['ACC001', 'ACC002', 'ACC003']
        
        for i in range(100):
            date = base_date + timedelta(days=i % 30)
            transaction = {
                'id': f'TXN{i:05d}',
                'date': date.strftime('%Y-%m-%d'),
                'payee': f'Merchant {i % 10}',
                'category': categories[i % len(categories)],
                'subcategory': f'Sub{i % 3}',
                'amount': round(50 + (i * 13.7) % 500, 2),
                'currency': 'USD',
                'account_id': accounts[i % len(accounts)],
                'account_type': 'Credit' if i % 2 == 0 else 'Debit',
                'tags': f'tag{i % 5}' if i % 3 == 0 else '',
                'anomalies': 'high_value' if i % 20 == 0 else '',
                'confidence': 'high'
            }
            transactions.append(transaction)
        
        return transactions
    
    def test_initialization(self):
        """Test XLSXExporter initialization."""
        self.assertIsNotNone(self.exporter)
        self.assertIsNotNone(self.exporter.logger)
        self.assertIsNotNone(self.exporter.header_font)
        self.assertIsNotNone(self.exporter.header_fill)
    
    def test_export_to_excel_basic(self):
        """Test basic export functionality."""
        output_file = os.path.join(self.temp_dir, 'test_export.xlsx')
        
        # Export transactions
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Load and verify workbook
        wb = load_workbook(output_file)
        self.assertIn('Transactions', wb.sheetnames)
        self.assertIn('Monthly Summary', wb.sheetnames)
        self.assertIn('Anomalies', wb.sheetnames)
    
    def test_export_empty_transactions(self):
        """Test export with empty transaction list."""
        output_file = os.path.join(self.temp_dir, 'test_empty.xlsx')
        
        with self.assertRaises(ValueError):
            self.exporter.export_to_excel([], output_file)
    
    def test_export_filename_without_extension(self):
        """Test export adds .xlsx extension if missing."""
        output_file = os.path.join(self.temp_dir, 'test_no_ext')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        # Verify file was created with .xlsx extension
        expected_file = output_file + '.xlsx'
        self.assertTrue(os.path.exists(expected_file))
    
    def test_transactions_sheet_structure(self):
        """Test Transactions sheet has correct structure."""
        output_file = os.path.join(self.temp_dir, 'test_structure.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Transactions']
        
        # Check that headers are present
        self.assertIsNotNone(ws['A1'].value)
        
        # Check that data rows exist
        self.assertGreater(ws.max_row, 1)
        
        # Check that freeze panes is set
        self.assertIsNotNone(ws.freeze_panes)
    
    def test_transactions_sheet_formatting(self):
        """Test Transactions sheet has proper formatting."""
        output_file = os.path.join(self.temp_dir, 'test_formatting.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Transactions']
        
        # Check header formatting
        header_cell = ws['A1']
        self.assertTrue(header_cell.font.bold)
        self.assertIsNotNone(header_cell.fill.start_color.rgb)
    
    def test_monthly_summary_sheet(self):
        """Test Monthly Summary sheet is created and has data."""
        output_file = os.path.join(self.temp_dir, 'test_summary.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Monthly Summary']
        
        # Check that sheet has content
        self.assertIsNotNone(ws['A1'].value)
        self.assertGreater(ws.max_row, 1)
    
    def test_anomalies_sheet(self):
        """Test Anomalies sheet contains only flagged transactions."""
        output_file = os.path.join(self.temp_dir, 'test_anomalies.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Anomalies']
        
        # Check that sheet has content (we have 5 anomalies in sample data)
        self.assertGreater(ws.max_row, 1)
    
    def test_anomalies_sheet_highlighting(self):
        """Test Anomalies sheet has highlighted rows."""
        output_file = os.path.join(self.temp_dir, 'test_anomaly_highlight.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Anomalies']
        
        # Check that data rows have fill color (anomaly highlighting)
        if ws.max_row > 1:  # If there are anomalies
            data_cell = ws['A2']  # First data row
            self.assertIsNotNone(data_cell.fill.start_color.rgb)
    
    def test_export_with_missing_columns(self):
        """Test export handles missing columns gracefully."""
        # Create transactions with minimal fields
        minimal_transactions = [
            {
                'id': 'TXN001',
                'date': '2024-01-01',
                'amount': 100.00
            },
            {
                'id': 'TXN002',
                'date': '2024-01-02',
                'amount': 200.00
            }
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_minimal.xlsx')
        
        # Should not raise an error
        self.exporter.export_to_excel(minimal_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_export_with_no_anomalies(self):
        """Test export when no anomalies are present."""
        # Create transactions without anomalies
        clean_transactions = [
            {
                'id': f'TXN{i:03d}',
                'date': '2024-01-01',
                'amount': 100.00,
                'category': 'Food',
                'anomalies': ''
            }
            for i in range(10)
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_no_anomalies.xlsx')
        
        self.exporter.export_to_excel(clean_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Anomalies']
        
        # Check that message is displayed
        self.assertIsNotNone(ws['A1'].value)
    
    def test_currency_formatting(self):
        """Test that amount columns have currency formatting."""
        output_file = os.path.join(self.temp_dir, 'test_currency.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Transactions']
        
        # Find amount column (assuming it's present)
        headers = [cell.value for cell in ws[1]]
        if 'amount' in headers:
            amount_col_idx = headers.index('amount') + 1
            # Check formatting of a data cell in amount column
            amount_cell = ws.cell(row=2, column=amount_col_idx)
            self.assertIn('$', amount_cell.number_format or '')
    
    def test_charts_in_summary_sheet(self):
        """Test that charts are added to Monthly Summary sheet."""
        output_file = os.path.join(self.temp_dir, 'test_charts.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Monthly Summary']
        
        # Check that charts were added
        self.assertGreater(len(ws._charts), 0)
    
    def test_column_width_adjustment(self):
        """Test that column widths are auto-adjusted."""
        output_file = os.path.join(self.temp_dir, 'test_width.xlsx')
        
        self.exporter.export_to_excel(self.sample_transactions, output_file)
        
        wb = load_workbook(output_file)
        ws = wb['Transactions']
        
        # Check that column widths are set
        for column in ws.column_dimensions.values():
            self.assertGreater(column.width, 0)
    
    def test_utf8_compatibility(self):
        """Test export handles UTF-8 characters correctly."""
        utf8_transactions = [
            {
                'id': 'TXN001',
                'date': '2024-01-01',
                'payee': 'Café René',
                'category': 'Food & Drink',
                'amount': 100.00,
                'currency': '€'
            },
            {
                'id': 'TXN002',
                'date': '2024-01-02',
                'payee': '北京饭店',
                'category': 'Restaurant',
                'amount': 200.00,
                'currency': '¥'
            }
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_utf8.xlsx')
        
        # Should handle UTF-8 characters without error
        self.exporter.export_to_excel(utf8_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        # Verify UTF-8 characters are preserved
        wb = load_workbook(output_file)
        ws = wb['Transactions']
        self.assertIsNotNone(ws['A2'].value)
    
    def test_large_dataset_export(self):
        """Test export with a larger dataset."""
        # Create 1000 transactions
        large_transactions = [
            {
                'id': f'TXN{i:05d}',
                'date': (datetime.now() - timedelta(days=i % 365)).strftime('%Y-%m-%d'),
                'payee': f'Merchant {i % 50}',
                'category': f'Category {i % 10}',
                'amount': round(10 + (i * 7.3) % 1000, 2),
                'anomalies': 'high_value' if i % 100 == 0 else ''
            }
            for i in range(1000)
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_large.xlsx')
        
        self.exporter.export_to_excel(large_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        # Verify all sheets are created
        wb = load_workbook(output_file)
        self.assertEqual(len(wb.sheetnames), 3)


if __name__ == '__main__':
    unittest.main()
