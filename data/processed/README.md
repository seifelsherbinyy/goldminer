# Processed Data Directory

This directory stores the processed data and SQLite database created by the GoldMiner ETL pipeline.

## Contents

- **goldminer.db**: SQLite database containing processed and unified data tables
- Database journals and temporary files (created automatically)

## Database Tables

The pipeline creates tables in the database with cleaned, normalized, and unified data:

- Default table name: `unified_data`
- Custom table names can be specified when running the pipeline

## Accessing the Database

### Using the CLI

List all tables:
```bash
python cli.py list
```

Analyze data:
```bash
python cli.py analyze --table unified_data
```

### Using Python

```python
from goldminer.etl import DatabaseManager

with DatabaseManager('data/processed/goldminer.db') as db:
    # Load data
    df = db.load_dataframe('unified_data')
    
    # List tables
    tables = db.list_tables()
    
    # Get table info
    info = db.get_table_info('unified_data')
```

## Notes

- Database files in this directory are gitignored by default
- The directory is created automatically if it doesn't exist
- Database path can be configured in `config.yaml`
