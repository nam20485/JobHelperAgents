import json
import gspread
from agno.tools import Toolkit
from agno.utils.log import logger
from datetime import datetime

class GoogleSheetsTools(Toolkit):
    def __init__(self, credentials_path: str, spreadsheet_name: str):
        super().__init__(name="google_sheets_tools")
        self.credentials_path = credentials_path
        self.spreadsheet_name = spreadsheet_name
        self.gc = None
        self.sh = None
        self.jobs_sheet = None
        self.apps_sheet = None
        self._authenticate()

        # Register the tools the Agent can access
        self.register_ops([
            self.add_job,
            self.get_new_jobs,
            self.get_user_preferences,
            self.promote_to_application
        ])

    def _authenticate(self):
        """Internal helper to auth with Google"""
        try:
            self.gc = gspread.service_account(filename=self.credentials_path)
            self.sh = self.gc.open(self.spreadsheet_name)

            # Initialize Worksheets
            # Ensure 'Jobs' sheet exists (usually Sheet1)
            try:
                self.jobs_sheet = self.sh.worksheet("Jobs")
            except:
                # Fallback if renamed or default
                self.jobs_sheet = self.sh.sheet1
                self.jobs_sheet.update_title("Jobs")

            # Ensure 'Applications' sheet exists
            try:
                self.apps_sheet = self.sh.worksheet("Applications")
            except:
                self.apps_sheet = self.sh.add_worksheet(title="Applications", rows=100, cols=10)
                # Add Headers
                self.apps_sheet.append_row(["Date Applied", "Company", "Role", "Status", "Link to Job", "Notes"])

            logger.info(f"Connected to Sheets: Jobs ({self.jobs_sheet.id}), Applications ({self.apps_sheet.id})")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")

    def add_job(self, company: str, role: str, url: str, location: str = "Remote"):
        """Adds a new job row to the 'Jobs' sheet."""
        try:
            date_found = datetime.now().strftime("%Y-%m-%d")

            # Deduplication
            try:
                cell = self.jobs_sheet.find(url)
                if cell:
                    return f"Job already exists at row {cell.row}"
            except gspread.exceptions.CellNotFound:
                pass

            # Columns: Date, Company, Role, Location, URL, Status, Notes, User Rating
            self.jobs_sheet.append_row([date_found, company, role, location, url, "New", "", ""])
            return f"Successfully added {role} at {company}."
        except Exception as e:
            return f"Error adding job: {e}"

    def get_new_jobs(self):
        """Retrieves jobs with status 'New' from 'Jobs' sheet."""
        try:
            all_records = self.jobs_sheet.get_all_records()
            new_jobs = [job for job in all_records if job.get('Status') == 'New']
            return json.dumps(new_jobs)
        except Exception as e:
            return f"Error retrieving jobs: {e}"

    def get_user_preferences(self):
        """Retrieves User Ratings for the learning loop."""
        try:
            all_records = self.jobs_sheet.get_all_records()
            rated_jobs = [
                {
                    "Role": job.get("Role"),
                    "Company": job.get("Company"),
                    "Rating": job.get("User Rating")
                }
                for job in all_records
                if str(job.get("User Rating", "")).strip() != ""
            ]
            return json.dumps(rated_jobs) if rated_jobs else "No user ratings found yet."
        except Exception as e:
            return f"Error retrieving preferences: {e}"

    def promote_to_application(self, job_url: str, status: str = "Applied"):
        """
        Promotes a job from the 'Jobs' sheet to the 'Applications' sheet.
        Creates BI-DIRECTIONAL LINKS between the two rows for easy navigation.
        """
        try:
            # 1. Find the Job in the main list
            try:
                job_cell = self.jobs_sheet.find(job_url)
                job_row_idx = job_cell.row
            except gspread.exceptions.CellNotFound:
                return "Job URL not found in Jobs sheet."

            # 2. Get Job Details (Assumes Col 2=Company, Col 3=Role)
            company = self.jobs_sheet.cell(job_row_idx, 2).value
            role = self.jobs_sheet.cell(job_row_idx, 3).value
            date_applied = datetime.now().strftime("%Y-%m-%d")

            # 3. Add to Applications Sheet
            # We add a placeholder for the link first
            self.apps_sheet.append_row([date_applied, company, role, status, "Linking...", ""])

            # Get the row index of the new application entry
            # (It's the last row since we just appended)
            app_row_idx = len(self.apps_sheet.get_all_values())

            # 4. Create Hyperlinks
            # Formula syntax: =HYPERLINK("#gid=SHEET_ID&range=A1", "Label")

            # Link from Apps -> Jobs
            job_gid = self.jobs_sheet.id
            link_to_job = f'=HYPERLINK("#gid={job_gid}&range=A{job_row_idx}", "View Listing")'
            self.apps_sheet.update_cell(app_row_idx, 5, link_to_job) # Col 5 is 'Link to Job'

            # Link from Jobs -> Apps
            app_gid = self.apps_sheet.id
            link_to_app = f'=HYPERLINK("#gid={app_gid}&range=A{app_row_idx}", "TRACKED: {status}")'
            self.jobs_sheet.update_cell(job_row_idx, 6, link_to_app) # Col 6 is 'Status'

            return f"Promoted {role} at {company} to Applications sheet (Row {app_row_idx}). Links created."

        except Exception as e:
            logger.error(f"Failed to promote application: {e}")
            return f"Error promoting application: {e}"
