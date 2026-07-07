# services/sheets_service.py

import streamlit as st
import gspread

from google.oauth2.service_account import Credentials

from config.settings import SHEET_NAME


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


creds = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]),
    scopes=SCOPES
)

client = gspread.authorize(creds)

spreadsheet = client.open(SHEET_NAME)

def get_sheet(sheet_name):

    return spreadsheet.worksheet(
        sheet_name
    )

def append_row(
    sheet_name,
    row_data
):

    sheet = get_sheet(
        sheet_name
    )

    sheet.append_row(
        row_data
    )