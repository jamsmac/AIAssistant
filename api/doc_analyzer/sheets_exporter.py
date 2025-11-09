"""
Google Sheets Exporter
Exports documentation analysis to Google Sheets with formatting
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)


class SheetsExporter:
    """Export documentation analysis to Google Sheets"""

    # Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    # Color scheme
    COLORS = {
        'header': {'red': 0.2, 'green': 0.4, 'blue': 0.8},  # Blue
        'GET': {'red': 0.2, 'green': 0.7, 'blue': 0.3},     # Green
        'POST': {'red': 0.3, 'green': 0.5, 'blue': 0.9},    # Blue
        'PUT': {'red': 0.9, 'green': 0.6, 'blue': 0.2},     # Orange
        'DELETE': {'red': 0.9, 'green': 0.3, 'blue': 0.3},  # Red
        'PATCH': {'red': 0.6, 'green': 0.4, 'blue': 0.8},   # Purple
    }

    def __init__(self):
        self.client: Optional[gspread.Client] = None
        self.credentials_available = False
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Sheets client with credentials"""
        try:
            # Try to load credentials from environment variable or file
            creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
            creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')

            if creds_json:
                # Load from JSON string
                creds_dict = json.loads(creds_json)
                credentials = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=self.SCOPES
                )
            elif creds_path and os.path.exists(creds_path):
                # Load from file
                credentials = Credentials.from_service_account_file(
                    creds_path,
                    scopes=self.SCOPES
                )
            else:
                logger.warning("No Google Sheets credentials found. Export will return formatted data only.")
                return

            self.client = gspread.authorize(credentials)
            self.credentials_available = True
            logger.info("Google Sheets client initialized successfully")

        except (DefaultCredentialsError, Exception) as e:
            logger.warning(f"Could not initialize Google Sheets client: {e}")
            self.credentials_available = False

    async def export_analysis(
        self,
        doc_source_id: str,
        api_name: str,
        api_version: str,
        spec_version: str,
        endpoints: List[Dict],
        schemas: Dict[str, Any],
        summary: str = ""
    ) -> Dict[str, Any]:
        """
        Export analysis to Google Sheets

        Returns:
            - If credentials available: {'sheet_url': 'https://...', 'sheet_id': '...'}
            - If no credentials: {'formatted_data': {...}, 'message': '...'}
        """
        try:
            # Prepare data
            summary_data = self._prepare_summary_data(
                api_name, api_version, spec_version,
                len(endpoints), len(schemas), doc_source_id
            )
            endpoints_data = self._prepare_endpoints_data(endpoints)
            schemas_data = self._prepare_schemas_data(schemas)
            schema_details = self._prepare_schema_details(schemas)

            # If no credentials, return formatted data
            if not self.credentials_available:
                return {
                    'success': False,
                    'message': 'Google Sheets credentials not configured. Set GOOGLE_SHEETS_CREDENTIALS_PATH or GOOGLE_SHEETS_CREDENTIALS_JSON environment variable.',
                    'formatted_data': {
                        'summary': summary_data,
                        'endpoints': endpoints_data,
                        'schemas': schemas_data,
                        'schema_details': schema_details
                    },
                    'instructions': 'You can copy the formatted_data and paste it into a spreadsheet manually.'
                }

            # Create spreadsheet
            sheet_name = f"{api_name} - API Analysis - {datetime.now().strftime('%Y-%m-%d')}"
            spreadsheet = self.client.create(sheet_name)

            # Share with owner (if specified)
            share_email = os.getenv('GOOGLE_SHEETS_SHARE_EMAIL')
            if share_email:
                spreadsheet.share(share_email, perm_type='user', role='owner')

            logger.info(f"Created spreadsheet: {spreadsheet.title} ({spreadsheet.id})")

            # Create and populate sheets
            self._create_summary_sheet(spreadsheet, summary_data)
            self._create_endpoints_sheet(spreadsheet, endpoints_data)
            self._create_schemas_sheet(spreadsheet, schemas_data)
            self._create_schema_details_sheet(spreadsheet, schema_details)

            # Remove default sheet if it exists
            try:
                default_sheet = spreadsheet.sheet1
                if default_sheet.title == "Sheet1":
                    spreadsheet.del_worksheet(default_sheet)
            except Exception:
                pass

            return {
                'success': True,
                'sheet_url': spreadsheet.url,
                'sheet_id': spreadsheet.id,
                'message': f'Successfully exported to Google Sheets: {spreadsheet.title}'
            }

        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Export failed: {str(e)}'
            }

    def _prepare_summary_data(
        self,
        api_name: str,
        api_version: str,
        spec_version: str,
        endpoint_count: int,
        schema_count: int,
        doc_id: str
    ) -> List[List[str]]:
        """Prepare summary data"""
        return [
            ['Field', 'Value'],
            ['API Name', api_name],
            ['API Version', api_version],
            ['Spec Version', spec_version],
            ['Total Endpoints', str(endpoint_count)],
            ['Total Schemas', str(schema_count)],
            ['Analyzed Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Document ID', doc_id],
        ]

    def _prepare_endpoints_data(self, endpoints: List[Dict]) -> List[List[str]]:
        """Prepare endpoints data"""
        data = [['Method', 'Path', 'Summary', 'Description', 'Parameters', 'Request Body', 'Responses']]

        for endpoint in endpoints:
            # Format parameters
            params = endpoint.get('parameters')
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except:
                    pass
            param_str = ', '.join([
                f"{p.get('name')} ({p.get('in')})"
                for p in (params or [])
            ]) if params else '-'

            # Format request body
            request_body = endpoint.get('request_body')
            if isinstance(request_body, str):
                try:
                    request_body = json.loads(request_body)
                except:
                    pass
            body_str = request_body.get('content_type', '-') if request_body else '-'

            # Format responses
            responses = endpoint.get('responses')
            if isinstance(responses, str):
                try:
                    responses = json.loads(responses)
                except:
                    pass
            response_str = ', '.join(responses.keys()) if responses else '-'

            data.append([
                endpoint.get('method', ''),
                endpoint.get('path', ''),
                endpoint.get('summary', ''),
                endpoint.get('description', ''),
                param_str,
                body_str,
                response_str
            ])

        return data

    def _prepare_schemas_data(self, schemas: Dict[str, Any]) -> List[List[str]]:
        """Prepare schemas overview data"""
        data = [['Schema Name', 'Type', 'Properties Count', 'Required Fields', 'Has SQL']]

        for schema_name, schema_info in schemas.items():
            properties = schema_info.get('properties', {})
            if isinstance(properties, str):
                try:
                    properties = json.loads(properties)
                except:
                    properties = {}

            required = schema_info.get('required_fields', [])
            required_str = ', '.join(required) if required else '-'

            has_sql = 'Yes' if schema_info.get('generated_sql') else 'No'

            data.append([
                schema_name,
                schema_info.get('schema_type', 'object'),
                str(len(properties)),
                required_str,
                has_sql
            ])

        return data

    def _prepare_schema_details(self, schemas: Dict[str, Any]) -> List[List[str]]:
        """Prepare detailed schema properties data"""
        data = [['Schema Name', 'Property Name', 'Type', 'Required', 'Description', 'Generated SQL']]

        for schema_name, schema_info in schemas.items():
            properties = schema_info.get('properties', {})
            if isinstance(properties, str):
                try:
                    properties = json.loads(properties)
                except:
                    properties = {}

            required = schema_info.get('required_fields', [])
            sql = schema_info.get('generated_sql', '')

            # Add a row for each property
            for prop_name, prop_info in properties.items():
                is_required = 'Yes' if prop_name in required else 'No'
                prop_type = prop_info.get('type', 'unknown')
                prop_desc = prop_info.get('description', '')

                data.append([
                    schema_name,
                    prop_name,
                    prop_type,
                    is_required,
                    prop_desc,
                    ''  # SQL only on first row
                ])

            # Add SQL on the first property row
            if properties and sql:
                data[len(data) - len(properties)][5] = sql

        return data

    def _create_summary_sheet(self, spreadsheet, data: List[List[str]]):
        """Create and format summary sheet"""
        try:
            sheet = spreadsheet.add_worksheet(title="Summary", rows=len(data), cols=2)
            sheet.update('A1', data)

            # Format header
            sheet.format('A1:B1', {
                'backgroundColor': self.COLORS['header'],
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'LEFT'
            })

            # Freeze header row
            sheet.freeze(rows=1)

            # Auto-resize columns
            sheet.columns_auto_resize(0, 1)

            logger.info("Created Summary sheet")
        except Exception as e:
            logger.error(f"Failed to create Summary sheet: {e}")

    def _create_endpoints_sheet(self, spreadsheet, data: List[List[str]]):
        """Create and format endpoints sheet"""
        try:
            sheet = spreadsheet.add_worksheet(title="Endpoints", rows=len(data), cols=7)
            sheet.update('A1', data)

            # Format header
            sheet.format('A1:G1', {
                'backgroundColor': self.COLORS['header'],
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER'
            })

            # Color-code HTTP methods
            for i, row in enumerate(data[1:], start=2):
                method = row[0]
                if method in self.COLORS:
                    sheet.format(f'A{i}', {
                        'backgroundColor': self.COLORS[method],
                        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                    })

            # Freeze header row
            sheet.freeze(rows=1)

            # Auto-resize columns
            sheet.columns_auto_resize(0, 6)

            logger.info(f"Created Endpoints sheet with {len(data)-1} endpoints")
        except Exception as e:
            logger.error(f"Failed to create Endpoints sheet: {e}")

    def _create_schemas_sheet(self, spreadsheet, data: List[List[str]]):
        """Create and format schemas overview sheet"""
        try:
            sheet = spreadsheet.add_worksheet(title="Schemas", rows=len(data), cols=5)
            sheet.update('A1', data)

            # Format header
            sheet.format('A1:E1', {
                'backgroundColor': self.COLORS['header'],
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER'
            })

            # Freeze header row
            sheet.freeze(rows=1)

            # Auto-resize columns
            sheet.columns_auto_resize(0, 4)

            logger.info(f"Created Schemas sheet with {len(data)-1} schemas")
        except Exception as e:
            logger.error(f"Failed to create Schemas sheet: {e}")

    def _create_schema_details_sheet(self, spreadsheet, data: List[List[str]]):
        """Create and format schema details sheet"""
        try:
            sheet = spreadsheet.add_worksheet(title="Schema Details", rows=len(data), cols=6)
            sheet.update('A1', data)

            # Format header
            sheet.format('A1:F1', {
                'backgroundColor': self.COLORS['header'],
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER'
            })

            # Freeze header row
            sheet.freeze(rows=1)

            # Auto-resize columns
            sheet.columns_auto_resize(0, 5)

            logger.info(f"Created Schema Details sheet with {len(data)-1} properties")
        except Exception as e:
            logger.error(f"Failed to create Schema Details sheet: {e}")


# Singleton instance
_exporter_instance: Optional[SheetsExporter] = None


def get_sheets_exporter() -> SheetsExporter:
    """Get singleton instance of SheetsExporter"""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = SheetsExporter()
    return _exporter_instance
