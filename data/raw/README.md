# Raw Data Directory

This directory is where you should place your raw data files for ingestion by the GoldMiner ETL pipeline.

## Supported File Formats

- **CSV files** (`.csv`)
- **Excel files** (`.xlsx`, `.xls`)

## Usage

1. Copy your data files into this directory
2. Run the pipeline using the CLI:
   ```bash
   python cli.py run data/raw/ --directory --analyze
   ```
   
3. Or use the Python API:
   ```python
   from goldminer.config import ConfigManager
   from goldminer.etl import ETLPipeline
   
   config = ConfigManager()
   pipeline = ETLPipeline(config)
   df = pipeline.run_pipeline('data/raw', is_directory=True)
   ```

## Example Data

To generate sample data for testing, run:
```bash
python example_usage.py
```

This will create sample CSV and Excel files in this directory.

## Notes

- Files in this directory are gitignored by default (except this README and .gitkeep)
- The pipeline will process all supported files in this directory
- Original files are not modified during processing
