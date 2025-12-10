from agno.tools import Toolkit
from agno.utils.log import logger
import pandas as pd
from jobspy import scrape_jobs

class JobSpyTools(Toolkit):
    def __init__(self):
        super().__init__(name="job_spy_tools")
        self.register_ops([self.find_jobs])

    def find_jobs(self, search_term: str, location: str = "Remote", results_wanted: int = 10):
        """
        Searches for jobs on LinkedIn, Indeed, and Glassdoor using JobSpy.
        """
        logger.info(f"Searching for {results_wanted} '{search_term}' jobs in {location}...")
        try:
            jobs_df = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor"],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_watchlist=["US"],
                hours_old=72
            )

            if jobs_df.empty:
                return "No jobs found."

            formatted_jobs = []
            for _, row in jobs_df.iterrows():
                formatted_jobs.append({
                    "Company": row.get('company'),
                    "Role": row.get('title'),
                    "Location": row.get('location'),
                    "URL": row.get('job_url'),
                    "Site": row.get('site')
                })

            return formatted_jobs
        except Exception as e:
            logger.error(f"JobSpy failed: {e}")
            return f"Error during job search: {e}"
