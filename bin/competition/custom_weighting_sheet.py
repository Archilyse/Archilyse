import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from common_utils.logger import logger
from handlers.competition.custom_weighting_sheet import CustomWeightingSheetDataProvider


class Requests:
    @staticmethod
    def insert_range(sheet_id, from_row, from_col, to_row, to_col):
        """This method is used to replicate existing formatting across a cell range"""
        return [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": from_col,
                        "endIndex": to_col,
                    },
                    "inheritFromBefore": True,
                }
            },
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": from_row,
                        "endIndex": to_row,
                    },
                    "inheritFromBefore": True,
                }
            },
        ]

    @staticmethod
    def update_cells(
        sheet_id, rows, update_number_format=False, from_row=0, from_col=0
    ):
        fields = f"userEnteredValue{',userEnteredFormat.numberFormat' if update_number_format else ''}"
        return {
            "updateCells": {
                "rows": [
                    {"values": [CellData.create(cell) for cell in cells]}
                    for cells in rows
                ],
                "fields": fields,
                "start": {
                    "sheetId": sheet_id,
                    "rowIndex": from_row,
                    "columnIndex": from_col,
                },
            }
        }

    @staticmethod
    def autoresize_columns(sheet_id, to_col, from_col=0):
        return {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": from_col,
                    "endIndex": to_col,
                }
            }
        }

    @staticmethod
    def update_sheet_title(sheet_id, sheet_title):
        return {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "title": sheet_title,
                },
                "fields": "title",
            }
        }

    @staticmethod
    def delete_sheet(sheet_id):
        return {"deleteSheet": {"sheetId": sheet_id}}


class CellData:
    @staticmethod
    def _get_user_entered_value(value):
        value_type = "stringValue"
        if isinstance(value, str):
            if value and value[0] == "=":
                value_type = "formulaValue"
        elif isinstance(value, bool):
            value_type = "boolValue"
        elif isinstance(value, (float, int)):
            value_type = "numberValue"
        return {"userEnteredValue": {value_type: value}}

    @staticmethod
    def _get_user_entered_format(unit):
        cell_format = {}
        if unit == "%":
            cell_format["numberFormat"] = {"type": "PERCENT", "pattern": "0.00%"}
        elif unit == "time_delta":
            cell_format["numberFormat"] = {"type": "NUMBER", "pattern": '0.00"h"'}
        elif unit == "sr":
            cell_format["numberFormat"] = {
                "type": "NUMBER",
                "pattern": f'0.0000"{unit}"',
            }
        elif unit:
            cell_format["numberFormat"] = {"type": "NUMBER", "pattern": f'0.00"{unit}"'}

        if cell_format:
            return {"userEnteredFormat": cell_format}
        return {}

    @classmethod
    def create(cls, value):
        unit = ""
        if isinstance(value, list):
            value, unit = value
        return {
            **cls._get_user_entered_value(value),
            **cls._get_user_entered_format(unit),
        }


class GoogleSheetsHandler:
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    @classmethod
    def get_credentials(cls):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("../../token.json"):
            creds = Credentials.from_authorized_user_file(
                "../../token.json", cls.SCOPES
            )

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    dict(
                        installed=dict(
                            auth_uri="https://accounts.google.com/o/oauth2/auth",
                            client_id=os.environ["GCLOUD_STORAGE_CLIENT_ID"],
                            client_secret=os.environ["GCLOUD_STORAGE_CLIENT_SECRET"],
                            token_uri="https://oauth2.googleapis.com/token",
                        ),
                    ),
                    cls.SCOPES,
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("../../token.json", "w") as token:
                token.write(creds.to_json())

        return creds

    @classmethod
    def get_service(cls):
        return build("sheets", "v4", credentials=cls.get_credentials())

    @classmethod
    def copy_template_spreadsheet(cls, title, service):
        template_spreadsheet_id = "1ZZTm6WavwgeOsN0jtlWs2q13Y1CQXqsgJ0XShDD1nOA"
        template_sheet_ids = [1337988148, 1610331123, 104852167]

        # create target spreadsheet
        target_spreadsheet = (
            service.spreadsheets()
            .create(
                body={"properties": {"title": title}},
                fields="spreadsheetId,spreadsheetUrl,sheets.properties.sheetId",
            )
            .execute()
        )

        # copy over the template sheets from the template spreadsheet
        target_sheet_ids = [
            service.spreadsheets()
            .sheets()
            .copyTo(
                spreadsheetId=template_spreadsheet_id,
                sheetId=sheet_id,
                body={
                    "destination_spreadsheet_id": target_spreadsheet.get(
                        "spreadsheetId"
                    )
                },
            )
            .execute()["sheetId"]
            for sheet_id in template_sheet_ids
        ]

        # rename the copied sheets (removing "Copy of ..." prefix) and delete Sheet1
        target_sheet_names = ["Scores", "Gewichtung", "Rohdaten"]
        body = {
            "requests": [
                Requests.delete_sheet(
                    target_spreadsheet["sheets"][0]["properties"]["sheetId"]
                ),
                *[
                    Requests.update_sheet_title(sheet_id, sheet_title)
                    for sheet_id, sheet_title in zip(
                        target_sheet_ids, target_sheet_names
                    )
                ],
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=target_spreadsheet.get("spreadsheetId"), body=body
        ).execute()

        return (
            target_spreadsheet["spreadsheetId"],
            target_spreadsheet["spreadsheetUrl"],
        ), target_sheet_ids

    @classmethod
    def update_spreadsheet(cls, service, spreadsheet_id, requests):
        return (
            service.spreadsheets()
            .batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests},
            )
            .execute()
        )


def generate_weighting_spreadsheet(competition_id):
    # get input data for the sheets
    data_provider = CustomWeightingSheetDataProvider(competition_id=competition_id)
    special_header = [[data_provider.get_header()]]
    scores_data, weighting_data, features_data = [
        data_provider.get_scores_data(),
        data_provider.get_weighting_data(),
        data_provider.get_features_data(),
    ]
    number_of_competitors = len(data_provider.competitor_names)

    # create a new spreadsheet from a template
    service = GoogleSheetsHandler.get_service()
    (
        (spreadsheet_id, spreadsheet_url),
        (scores_sheet_id, weighting_sheet_id, features_sheet_id),
    ) = GoogleSheetsHandler.copy_template_spreadsheet(
        service=service, title=data_provider.get_title()
    )

    requests = []

    # add ranges inheriting the existing format
    requests.extend(
        request
        for sheet_id, from_row, from_col, to_row, to_col in [
            (scores_sheet_id, 7, 2, len(scores_data) - 1, number_of_competitors),
            (weighting_sheet_id, 8, 2, len(weighting_data) + 6, 2),
            (features_sheet_id, 7, 2, len(features_data) + 5, number_of_competitors),
        ]
        for request in Requests.insert_range(
            sheet_id, from_row, from_col, to_row, to_col
        )
    )

    # update the sheets with the data
    data = [
        {"sheet_id": scores_sheet_id, "from_row": 5, "rows": scores_data},
        {"sheet_id": weighting_sheet_id, "from_row": 7, "rows": weighting_data},
        {
            "sheet_id": features_sheet_id,
            "from_row": 5,
            "rows": features_data,
            "update_number_format": True,
        },
    ]
    special_headers = [
        {"sheet_id": sheet_id, "from_row": 1, "rows": special_header}
        for sheet_id in [scores_sheet_id, weighting_sheet_id, features_sheet_id]
    ]
    requests.extend(Requests.update_cells(**args) for args in special_headers + data)

    # resize the columns
    requests.extend(
        Requests.autoresize_columns(sheet_id=sheet_id, to_col=to_col)
        for sheet_id, to_col in [
            (scores_sheet_id, number_of_competitors + 1),
            (weighting_sheet_id, 5),
            (features_sheet_id, number_of_competitors + 1),
        ]
    )

    GoogleSheetsHandler.update_spreadsheet(
        service=service, spreadsheet_id=spreadsheet_id, requests=requests
    )

    logger.info(f"Your spreadsheet is ready: {spreadsheet_url}")


if __name__ == "__main__":
    generate_weighting_spreadsheet(competition_id=11)
