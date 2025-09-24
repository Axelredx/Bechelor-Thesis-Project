import pandas as pd
import sys
from pathlib import Path
from utility.error_logger import Logger

#####################################
# EXCEL/OPENDOCUMENT HANDLING TOOLS #
#####################################

class ExcelAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    '''analyze excel files and send to claude for classification 
        (it supports: new xls file formats, .xls, .xlsx, .xlsm, .xlsb, .odf, .ods, .odt, Binary Excel files)'''
    def analyze_excel(self, excel_file_path: Path, company_name: str) -> tuple[Path, dict, str]:
        try:
            # Read the Excel file (all sheets) - pandas handles various formats w various engine based on file passed
            excel_file = pd.ExcelFile(excel_file_path)

            analysis_data = {
                "file_info": {
                    "name": excel_file_path.name,
                    "company": company_name,
                    "sheets": excel_file.sheet_names,
                    "total_sheets": len(excel_file.sheet_names)
                },
                "sheets_data": []
            }

            # Max 3 sheets considered
            for sheet_considered in excel_file.sheet_names[:3]:
                try:
                    data_frame = pd.read_excel(excel_file_path, sheet_name=sheet_considered)

                    structural_sheet_info = {
                        "sheet_name": sheet_considered,
                        "rows": len(data_frame),
                        "columns": len(data_frame.columns),
                        "column_names": data_frame.columns.tolist()
                    }

                    if not data_frame.empty:
                        # Convert NaN to [EMPTY] for better comprehension of Claude
                        # + ONLY take first 30 ROWS of the sheet
                        sample_df = data_frame.head(30).fillna("[EMPTY]")
                        structural_sheet_info["sample_data"] = sample_df.to_dict(orient='records')

                        # Add type of data
                        structural_sheet_info["column_types"] = {
                            col: str(dtype) for col, dtype in data_frame.dtypes.items()
                        }

                        # Now consider columns with numeric data
                        numeric_cols = data_frame.select_dtypes(include=['number']).columns
                        if len(numeric_cols) > 0:
                            # Add generic numeric summary
                            structural_sheet_info["numeric_summary"] = {
                                col: {
                                    "min": float(data_frame[col].min()) if pd.notna(data_frame[col].min()) else None,
                                    "max": float(data_frame[col].max()) if pd.notna(data_frame[col].max()) else None,
                                    "non_null_count": int(data_frame[col].count())
                                }
                                # limit max columns to first 15
                                for col in numeric_cols[:15]
                            }

                    analysis_data["sheets_data"].append(structural_sheet_info)
                    self.logger.write_info_in_log_file(f"(at func: analyze_excel) Successfully processed sheet '{sheet_considered}' in {excel_file_path}\n")
                
                except Exception as sheet_error:
                    self.logger.write_warning_in_log_file(f"(at func: analyze_excel) Error reading sheet '{sheet_considered}': {sheet_error}\n")
                    analysis_data["sheets_data"].append({
                        "sheet_name": sheet_considered,
                        "error": str(sheet_error)
                    })

            return excel_file_path, analysis_data, company_name
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_excel) Error processing Excel file {excel_file_path}: {e}\n")
            return excel_file_path, {}, company_name