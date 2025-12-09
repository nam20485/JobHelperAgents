import json
from datetime import datetime
from typing import Optional

import gspread
from agno.tools import Toolkit
from agno.utils.log import logger
from gspread import Spreadsheet, Worksheet
from gspread.exceptions import SpreadsheetNotFound


class GoogleSheetsTools(Toolkit):
    """
    A toolkit for managing job tracking in Google Sheets.
    Provides methods to add jobs, retrieve new jobs, and update job statuses.
    """

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Initialize the GoogleSheetsTools toolkit.

        Args:
            credentials_path: Path to the Google service account credentials JSON file
            spreadsheet_id: ID of the Google Sheet to use for job tracking
        """
        super().__init__(name="google_sheets_tools")
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.gc: Optional[gspread.Client] = None
        self.sh: Optional[Spreadsheet] = None
        self._authenticate()

        # Register the tools the Agent can access
        self.register(self.add_job)
        self.register(self.get_new_jobs)
        self.register(self.update_job_status)
        self.register(self.get_all_jobs)
        self.register(self.check_job_exists)

    def _authenticate(self) -> bool:
        """
        Internal helper to authenticate with Google Sheets API.

        Returns:
            True if authentication successful, False otherwise.
        """
        try:
            self.gc = gspread.service_account(filename=self.credentials_path)
            self.sh = self.gc.open_by_key(self.spreadsheet_id)
            logger.info(f"Successfully connected to Sheet: {self.spreadsheet_id}")
            return True
        except FileNotFoundError:
            logger.error(
                f"Credentials file not found: {self.credentials_path}. "
                "Please ensure you have a valid service account JSON file."
            )
        except SpreadsheetNotFound:
            logger.error(
                f"Spreadsheet '{self.spreadsheet_id}' not found. "
                "Make sure the sheet exists and is shared with your service account."
            )
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
        return False

    def _get_worksheet(self) -> Optional[Worksheet]:
        """Get the first worksheet, handling potential None values."""
        if self.sh is None:
            logger.error(
                "Not connected to Google Sheets. Authentication may have failed."
            )
            return None
        try:
            return self.sh.sheet1
        except Exception as e:
            logger.error(f"Error accessing worksheet: {e}")
            return None

    def _ensure_headers(self, worksheet: Worksheet) -> None:
        """Ensure the worksheet has the expected headers."""
        expected_headers = [
            "Date",
            "Site",
            "Role",
            "Company",
            "Type",
            "Posting Link",
            "URL",
            "Status",
            "Application Date",
            "Resume",
            "Cover Letter",
            "Notes",
        ]
        try:
            first_row = worksheet.row_values(1)
            if not first_row:
                # Sheet is empty, add headers
                worksheet.append_row(expected_headers)
                logger.info("Added headers to empty sheet") fb
        except Exception as e:
            logger.debug(f"Could not check/add headers: {e}")

    def add_job(
        self,
        company: str,
        role: str,
        url: str,
        location: str = "Remote",
        source: str = "",
        notes: str = "",
    ) -> str:
        """
        Adds a new job row to the Google Sheet.
        Use this tool when you find a new job posting that matches criteria.

        Args:
            company: Company name
            role: Job title/role
            url: URL to the job posting
            location: Job location (default: "Remote")
            source: Where the job was found (e.g., "linkedin", "glassdoor")
            notes: Any additional notes about the job

        Returns:
            Success or error message
        """
        worksheet = self._get_worksheet()
        if worksheet is None:
            return "Error: Could not access the Google Sheet. Check authentication."

        try:
            # Ensure headers exist
            self._ensure_headers(worksheet)

            date_found = datetime.now().strftime("%Y-%m-%d")

            # Check for duplicates (basic check on URL)
            # In newer gspread, find() returns None instead of raising exception
            cell = worksheet.find(url)
            if cell is not None:
                return f"Job already exists in sheet at row {cell.row}"

            # Row format: Date, Company, Role, Location, URL, Status, Notes, Source
            worksheet.append_row(
                [
                    date_found,
                    company,
                    role,
                    location,
                    url,
                    "New",
                    notes,
                    source,
                ]
            )
            return f"Successfully added '{role}' at '{company}' to the sheet."
        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return f"Error adding job: {e}"

    def get_new_jobs(self) -> str:
        """
        Retrieves all jobs with status 'New'.
        Use this to find jobs that need resume tailoring or application.

        Returns:
            JSON string containing list of new jobs, or error message
        """
        worksheet = self._get_worksheet()
        if worksheet is None:
            return json.dumps({"error": "Could not access the Google Sheet"})

        try:
            all_records = worksheet.get_all_records()
            new_jobs = [job for job in all_records if job.get("Status") == "New"]
            return json.dumps({"count": len(new_jobs), "jobs": new_jobs}, indent=2)
        except Exception as e:
            logger.error(f"Error retrieving jobs: {e}")
            return json.dumps({"error": str(e)})

    def get_all_jobs(self, status: Optional[str] = None) -> str:
        """
        Retrieves all jobs from the sheet, optionally filtered by status.

        Args:
            status: Optional status to filter by (e.g., "New", "Applied", "Tailored", "Interview", "Rejected")

        Returns:
            JSON string containing list of jobs, or error message
        """
        worksheet = self._get_worksheet()
        if worksheet is None:
            return json.dumps({"error": "Could not access the Google Sheet"})

        try:
            all_records = worksheet.get_all_records()
            if status:
                filtered_jobs = [
                    job
                    for job in all_records
                    if str(job.get("Status", "")).lower() == status.lower()
                ]
                return json.dumps(
                    {
                        "status_filter": status,
                        "count": len(filtered_jobs),
                        "jobs": filtered_jobs,
                    },
                    indent=2,
                )
            return json.dumps(
                {"count": len(all_records), "jobs": all_records}, indent=2
            )
        except Exception as e:
            logger.error(f"Error retrieving jobs: {e}")
            return json.dumps({"error": str(e)})

    def check_job_exists(self, url: str) -> str:
        """
        Check if a job with the given URL already exists in the sheet.

        Args:
            url: The job posting URL to check

        Returns:
            JSON string with exists boolean and row number if found
        """
        worksheet = self._get_worksheet()
        if worksheet is None:
            return json.dumps({"error": "Could not access the Google Sheet"})

        try:
            cell = worksheet.find(url)
            if cell is not None:
                # Get the full row data
                row_data = worksheet.row_values(cell.row)
                return json.dumps(
                    {
                        "exists": True,
                        "row": cell.row,
                        "data": {
                            "date": row_data[0] if len(row_data) > 0 else "",
                            "company": row_data[1] if len(row_data) > 1 else "",
                            "role": row_data[2] if len(row_data) > 2 else "",
                            "location": row_data[3] if len(row_data) > 3 else "",
                            "url": row_data[4] if len(row_data) > 4 else "",
                            "status": row_data[5] if len(row_data) > 5 else "",
                            "notes": row_data[6] if len(row_data) > 6 else "",
                            "source": row_data[7] if len(row_data) > 7 else "",
                        },
                    },
                    indent=2,
                )
            return json.dumps({"exists": False})
        except Exception as e:
            logger.error(f"Error checking job: {e}")
            return json.dumps({"error": str(e)})

    def update_job_status(
        self,
        url: str,
        new_status: str,
        notes: str = "",
    ) -> str:
        """
        Updates the status of a job in the sheet.
        Use this after tailoring a resume (Status -> 'Tailored') or applying (Status -> 'Applied').

        Common statuses:
        - "New": Just added, not yet processed
        - "Tailored": Resume has been tailored for this job
        - "Applied": Application submitted
        - "Interview": Got an interview
        - "Rejected": Application rejected
        - "Offer": Received an offer
        - "Declined": Declined to apply or declined offer

        Args:
            url: The job posting URL to identify the row
            new_status: The new status to set
            notes: Optional notes to add (appends to existing notes)

        Returns:
            Success or error message
        """
        worksheet = self._get_worksheet()
        if worksheet is None:
            return "Error: Could not access the Google Sheet. Check authentication."

        try:
            cell = worksheet.find(url)
            if cell is None:
                return f"Job URL not found in sheet: {url}"

            # Column indices (1-based)
            status_col_index = 6
            notes_col_index = 7

            # Update status
            worksheet.update_cell(cell.row, status_col_index, new_status)

            # Update notes (append if there are existing notes)
            if notes:
                try:
                    existing_notes = (
                        worksheet.cell(cell.row, notes_col_index).value or ""
                    )
                    if existing_notes:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        updated_notes = f"{existing_notes}\n[{timestamp}] {notes}"
                    else:
                        updated_notes = notes
                    worksheet.update_cell(cell.row, notes_col_index, updated_notes)
                except Exception as e:
                    logger.warning(f"Could not update notes: {e}")

            return f"Updated job to status: '{new_status}'"
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            return f"Error updating status: {e}"
