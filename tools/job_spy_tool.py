import json
import re
import subprocess
import sys
from enum import Enum
from typing import Optional
from urllib.parse import quote_plus

from agno.tools import Toolkit
from agno.utils.log import logger

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
except ImportError:
    logger.error(
        "Playwright dependencies not installed. Run: pip install playwright playwright-stealth"
    )
    raise


class JobSite(str, Enum):
    """Supported job search sites."""

    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    GOOGLE = "google"
    INDEED = "indeed"
    LEVELSFYI = "levelsfyi"


class JobSpyTools(Toolkit):
    """
    A toolkit for scraping job listings from multiple job boards using Playwright.
    Supports LinkedIn, Glassdoor, Google Jobs, Levels.fyi, and Indeed with stealth mode to avoid detection.

    Levels.fyi is particularly useful as it includes compensation data for job listings.
    """

    SUPPORTED_SITES = [site.value for site in JobSite]

    # Condensed list from 2024/2025 reports (Glassdoor, Forbes, etc.)
    BEST_PLACES_TO_WORK = {
        "google", "zappos", "bluecore", "airbnb", "costco", "zoom", "ikea", "cisco", "ibm", 
        "squarespace", "warby parker", "healthpeak", "mighty citizen", "supplyforce", "pultegroup",
        "progressive insurance", "dow", "delta", "adobe", "boston scientific", "canva", "capital one",
        "chase", "deloitte", "epsilon", "ey", "hyundai", "intuit", "pfizer", "sap", "starbucks",
        "verizon", "motorola solutions", "siemens", "omnea", "nvidia", "microsoft", "bain & company",
        "atlassian", "salesforce", "mathworks", "lyulfe", "procore", "servicenow", "hubspot",
        "workday", "fidelity investments", "ally", "mastercard", "apple", "meta"
    }

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the JobSpyTools toolkit.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Default timeout for page operations in milliseconds (default: 30000)
        """
        super().__init__(name="job_spy_tools")
        self.headless = headless
        self.timeout = timeout

        # Ensure Playwright browsers are installed
        self._ensure_browsers_installed()

        # Register the tools the Agent can access
        self.register(self.find_jobs)

    def _calculate_salary_penalty(self, salary_text: str) -> int:
        """
        Calculate penalty points based on salary.
        -1 point for every $10k less than $200k base salary.
        """
        if not salary_text:
            return 0  # No data, no emoji, also no penalty?? Or default penalty? Let's say 0.

        # Normalize text
        text = salary_text.lower().replace(",", "").replace("$", "")
        
        # Extract numbers (simple regex for "120k", "120000", "120-150k")
        # Multipliers
        multiplier = 1
        if "k" in text:
            multiplier = 1000
            text = text.replace("k", "")
        
        # Find all numbers
        import re
        matches = re.findall(r"(\d+(?:\.\d+)?)", text)
        if not matches:
            return 0

        try:
            # Take the first number found as the base/lower bound
            # e.g. "120 - 150" -> 120
            # e.g. "120000" -> 120000
            # e.g. "80 - 90/hr" -> Handling hourly is tough without more context.
            # Assuming annual if > 1000, else hourly?
            
            val = float(matches[0]) * multiplier
            
            # Heuristic: If hourly (< 200), convert to annual (x 2000)
            if val < 200:
                val *= 2000
            
            # Target is 200k
            target = 200000
            if val >= target:
                return 0
            
            # Deficit
            deficit = target - val
            # Points = deficit / 10000
            points = int(deficit / 10000)
            return -points
            
        except Exception:
            return 0

    def _is_best_place_to_work(self, company_name: str) -> bool:
        """Check if company is in the best places to work list."""
        if not company_name:
            return False
            
        name = company_name.lower().strip()
        
        # Exact match or substring match? 
        # "Google Inc" vs "Google"
        # Let's check if any key in set is a substring of the input name, or vice versa
        
        for best_company in self.BEST_PLACES_TO_WORK:
            # Check exact or word boundary match would be better, but simple substring for now
            if best_company in name:
                return True
        return False

    def _is_recent_job(self, date_text: str) -> bool:
        """
        Check if job was posted within the last 3 days.
        Hands relative times ("2 days ago", "just now") and ISO dates.
        """
        if not date_text:
            return False
            
        text = date_text.lower()
        
        # Immediate/Very recent
        if any(x in text for x in ["today", "just", "hour", "minute", "second", "new"]):
            return True
            
        # Check specific day counts
        import re
        # Match "1 day", "2 days", "3d", "2d"
        # If it says "10 days", we want to know it's > 3
        
        # Regex for "N day" or "Nd"
        match = re.search(r"(\d+)\s*d", text)
        if match:
            days = int(match.group(1))
            return days <= 3
            
        return False

    def calculate_rating(self, job: dict) -> int:
        """
        Calculate job rating based on:
        +1: Easy Apply (not yet scraped reliably, defaulting 0)
        +1: Contract
        +1: Remote
        +1: C# listed
        +1: C++ listed
        +1: Posted within 3 days
        +1: Best Places to Work
        -1: Full Onsite
        -1 per $10k < $200k salary
        """
        score = 0
        
        # Text fields
        title = job.get("title", "").lower()
        snippet = job.get("snippet", "").lower() # Indeed has snippets
        location = job.get("location", "").lower()
        # combine for keyword search
        full_text = f"{title} {snippet}"
        
        # Positive Attributes
        # Easy Apply - placeholder
        if job.get("easy_apply"):
            score += 1
            
        # Recent Job (< 3 days)
        if self._is_recent_job(job.get("date_posted", "")):
            score += 1

        # Best Places to Work
        if self._is_best_place_to_work(job.get("company", "")):
             score += 1

        # Contract
        # Check job type or title
        # job_type arg passed to search isn't saved in job dict usually, but we can check title
        if "contract" in title or "contract" in snippet:
            score += 1
            
        # Remote
        is_remote = False
        if "remote" in location or job.get("remote") is True:
            score += 1
            is_remote = True
            
        # C#
        if "c#" in full_text or "c sharp" in full_text:
            score += 1
            
        # C++
        if "c++" in full_text or "cpp" in full_text:
            score += 1
            
        # Negative Attributes
        # Full Onsite (not hybrid, not remote)
        # If matches "onsite" or logic implies it? 
        # Easier: If not remote and not hybrid -> Onsite
        is_hybrid = "hybrid" in location
        if not is_remote and not is_hybrid:
            score -= 1
            
        # Salary Penalty
        salary_text = job.get("salary", "")
        score += self._calculate_salary_penalty(salary_text)
        
        return score

    def _ensure_browsers_installed(self) -> None:
        """
        Check if Playwright browsers are installed and install them if needed.
        This runs `playwright install chromium` if the browser is not found.
        """
        try:
            # Try to launch a browser to check if it's installed
            with Stealth().use_sync(sync_playwright()) as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
                logger.debug("Playwright Chromium browser is already installed")
        except Exception as e:
            error_msg = str(e).lower()
            if "executable doesn't exist" in error_msg or "browser" in error_msg:
                logger.info("Playwright browsers not found. Installing Chromium...")
                try:
                    # Run playwright install chromium
                    result = subprocess.run(
                        [sys.executable, "-m", "playwright", "install", "chromium"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    logger.info("Successfully installed Playwright Chromium browser")
                    if result.stdout:
                        logger.debug(f"Install output: {result.stdout}")
                except subprocess.CalledProcessError as install_error:
                    logger.error(
                        f"Failed to install Playwright browsers: {install_error.stderr}"
                    )
                    raise RuntimeError(
                        "Failed to install Playwright browsers. "
                        "Please run manually: playwright install chromium"
                    ) from install_error
            else:
                # Some other error, re-raise
                logger.error(f"Unexpected error checking browser installation: {e}")
                raise

    # =========================================================================
    # LinkedIn Methods
    # =========================================================================

    def _build_linkedin_url(
        self,
        search_term: str,
        location: str,
        start: int = 0,
        days_ago: Optional[int] = None,
        job_type: Optional[str] = None,
        remote: bool = False,
    ) -> str:
        """Build LinkedIn Jobs search URL with parameters."""
        base_url = "https://www.linkedin.com/jobs/search/"
        params = [
            f"keywords={quote_plus(search_term)}",
            f"location={quote_plus(location)}",
            f"start={start}",
            "sortBy=DD",  # Sort by most recent
        ]

        # Time filter (f_TPR): r86400=24h, r604800=week, r2592000=month
        if days_ago:
            if days_ago <= 1:
                params.append("f_TPR=r86400")
            elif days_ago <= 7:
                params.append("f_TPR=r604800")
            elif days_ago <= 30:
                params.append("f_TPR=r2592000")

        # Job type filter (f_JT): F=Full-time, P=Part-time, C=Contract, T=Temporary, I=Internship
        if job_type:
            job_type_map = {
                "fulltime": "f_JT=F",
                "parttime": "f_JT=P",
                "contract": "f_JT=C",
                "temporary": "f_JT=T",
                "internship": "f_JT=I",
            }
            if job_type.lower() in job_type_map:
                params.append(job_type_map[job_type.lower()])

        # Remote filter (f_WT): 2=Remote, 1=On-site, 3=Hybrid
        if remote:
            params.append("f_WT=2")

        return f"{base_url}?{'&'.join(params)}"

    def _extract_linkedin_jobs(self, page) -> list[dict]:
        """Extract job listings from LinkedIn search results page."""
        jobs = []

        try:
            # Wait for job cards to load - LinkedIn uses various selectors
            page.wait_for_selector(
                ".jobs-search__results-list, .scaffold-layout__list, ul.jobs-search-results__list",
                timeout=15000,
            )

            # Scroll to load more jobs
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1000)")
                page.wait_for_timeout(500)

            # Get all job cards
            job_cards = page.query_selector_all(
                ".base-card, .job-search-card, li.jobs-search-results__list-item, .jobs-search-results__list-item"
            )

            for card in job_cards:
                try:
                    job = {}

                    # Extract job title
                    title_elem = card.query_selector(
                        ".base-search-card__title, .job-search-card__title, h3.base-search-card__title, a.job-card-list__title"
                    )
                    if title_elem:
                        job["title"] = title_elem.inner_text().strip()

                    # Extract company name
                    company_elem = card.query_selector(
                        ".base-search-card__subtitle, .job-search-card__subtitle, h4.base-search-card__subtitle, .job-card-container__company-name"
                    )
                    if company_elem:
                        job["company"] = company_elem.inner_text().strip()

                    # Extract location
                    location_elem = card.query_selector(
                        ".job-search-card__location, .base-search-card__metadata, span.job-card-container__metadata-item"
                    )
                    if location_elem:
                        job["location"] = location_elem.inner_text().strip()

                    # Extract job URL
                    link_elem = card.query_selector(
                        "a.base-card__full-link, a.job-card-list__title, a.job-card-container__link"
                    )
                    if link_elem:
                        href = link_elem.get_attribute("href")
                        if href:
                            # Clean up URL (remove tracking params)
                            job["url"] = href.split("?")[0] if "?" in href else href

                            # Extract job ID from URL
                            job_id_match = re.search(r"-(\d+)\??", href)
                            if job_id_match:
                                job["job_id"] = job_id_match.group(1)

                    # Extract date posted
                    date_elem = card.query_selector(
                        "time, .job-search-card__listdate, .job-card-container__listed-time"
                    )
                    if date_elem:
                        datetime_attr = date_elem.get_attribute("datetime")
                        if datetime_attr:
                            job["date_posted"] = datetime_attr
                        else:
                            job["date_posted"] = date_elem.inner_text().strip()

                    # Extract salary if available
                    salary_elem = card.query_selector(
                        ".job-search-card__salary-info, .salary-info"
                    )
                    if salary_elem:
                        job["salary"] = salary_elem.inner_text().strip()

                    # Only add job if we have at least title and company
                    if job.get("title") and job.get("company"):
                        job["source"] = "linkedin"
                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error extracting LinkedIn job card: {e}")
                    continue

        except PlaywrightTimeout:
            logger.warning("Timeout waiting for LinkedIn job cards to load")
        except Exception as e:
            logger.error(f"Error extracting LinkedIn jobs: {e}")

        return jobs

    # =========================================================================
    # Glassdoor Methods
    # =========================================================================

    def _build_glassdoor_url(
        self,
        search_term: str,
        location: str,
        start: int = 0,
        days_ago: Optional[int] = None,
        job_type: Optional[str] = None,
        remote: bool = False,
    ) -> str:
        """Build Glassdoor Jobs search URL with parameters."""
        # Glassdoor uses a different URL structure
        base_url = "https://www.glassdoor.com/Job/jobs.htm"
        params = [
            f"sc.keyword={quote_plus(search_term)}",
            f"locT=C&locKeyword={quote_plus(location)}",
        ]

        # Pagination (Glassdoor uses page numbers)
        page_num = (start // 30) + 1
        if page_num > 1:
            params.append(f"p={page_num}")

        # Date posted filter
        if days_ago:
            if days_ago <= 1:
                params.append("fromAge=1")
            elif days_ago <= 3:
                params.append("fromAge=3")
            elif days_ago <= 7:
                params.append("fromAge=7")
            elif days_ago <= 14:
                params.append("fromAge=14")
            else:
                params.append("fromAge=30")

        # Remote filter
        if remote:
            params.append("remoteWorkType=1")

        return f"{base_url}?{'&'.join(params)}"

    def _extract_glassdoor_jobs(self, page) -> list[dict]:
        """Extract job listings from Glassdoor search results page."""
        jobs = []

        try:
            # Wait for job listings to load
            page.wait_for_selector(
                '[data-test="jobListing"], .JobsList_jobListItem__JBBUV, ul.JobsList_jobsList__lqjTr',
                timeout=15000,
            )

            # Scroll to load more
            for _ in range(2):
                page.evaluate("window.scrollBy(0, 800)")
                page.wait_for_timeout(500)

            # Get all job cards
            job_cards = page.query_selector_all(
                '[data-test="jobListing"], li.JobsList_jobListItem__JBBUV, .react-job-listing'
            )

            for card in job_cards:
                try:
                    job = {}

                    # Extract job title
                    title_elem = card.query_selector(
                        '[data-test="job-title"], .JobCard_jobTitle__GLyJ1, a.jobLink'
                    )
                    if title_elem:
                        job["title"] = title_elem.inner_text().strip()

                    # Extract company name
                    company_elem = card.query_selector(
                        '[data-test="employer-name"], .EmployerProfile_employerName__Xemli, .jobLink span'
                    )
                    if company_elem:
                        job["company"] = company_elem.inner_text().strip()

                    # Extract location
                    location_elem = card.query_selector(
                        '[data-test="emp-location"], .JobCard_location__N_iYE, .location'
                    )
                    if location_elem:
                        job["location"] = location_elem.inner_text().strip()

                    # Extract job URL
                    link_elem = card.query_selector(
                        'a[data-test="job-title"], a.JobCard_jobTitle__GLyJ1, a.jobLink'
                    )
                    if link_elem:
                        href = link_elem.get_attribute("href")
                        if href:
                            if href.startswith("/"):
                                job["url"] = f"https://www.glassdoor.com{href}"
                            else:
                                job["url"] = href

                    # Extract salary if available
                    salary_elem = card.query_selector(
                        '[data-test="detailSalary"], .JobCard_salaryEstimate__QpbTW, .salary-estimate'
                    )
                    if salary_elem:
                        job["salary"] = salary_elem.inner_text().strip()

                    # Extract rating if available
                    rating_elem = card.query_selector(
                        '[data-test="rating"], .JobCard_rating__xRaou'
                    )
                    if rating_elem:
                        job["company_rating"] = rating_elem.inner_text().strip()

                    # Only add job if we have at least title and company
                    if job.get("title") and job.get("company"):
                        job["source"] = "glassdoor"
                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error extracting Glassdoor job card: {e}")
                    continue

        except PlaywrightTimeout:
            logger.warning("Timeout waiting for Glassdoor job cards to load")
        except Exception as e:
            logger.error(f"Error extracting Glassdoor jobs: {e}")

        return jobs

    # =========================================================================
    # Google Jobs Methods
    # =========================================================================

    def _build_google_jobs_url(
        self,
        search_term: str,
        location: str,
        days_ago: Optional[int] = None,
        job_type: Optional[str] = None,
        remote: bool = False,
    ) -> str:
        """Build Google Jobs search URL with parameters."""
        # Google Jobs is accessed through Google Search with specific parameters
        query = f"{search_term} jobs"
        if location and location.lower() != "remote":
            query += f" in {location}"
        if remote:
            query += " remote"

        base_url = "https://www.google.com/search"
        params = [
            f"q={quote_plus(query)}",
            "ibp=htl;jobs",  # This triggers the Jobs panel
        ]

        # Date filter
        if days_ago:
            if days_ago <= 1:
                params.append("chips=date_posted:today")
            elif days_ago <= 3:
                params.append("chips=date_posted:3days")
            elif days_ago <= 7:
                params.append("chips=date_posted:week")
            else:
                params.append("chips=date_posted:month")

        return f"{base_url}?{'&'.join(params)}"

    def _extract_google_jobs(self, page) -> list[dict]:
        """Extract job listings from Google Jobs search results."""
        jobs = []

        try:
            # Wait for Google Jobs panel to load
            page.wait_for_selector(
                '.iFjolb, [jsname="yEVEwb"], .gws-plugins-horizon-jobs__li-ed',
                timeout=15000,
            )

            # Click on jobs to expand the list
            page.wait_for_timeout(2000)

            # Get all job cards
            job_cards = page.query_selector_all(
                '.iFjolb, li.iFjolb, [jsname="yEVEwb"], .gws-plugins-horizon-jobs__li-ed'
            )

            for card in job_cards:
                try:
                    job = {}

                    # Extract job title
                    title_elem = card.query_selector(
                        '.BjJfJf, [role="heading"], .sH3zFd'
                    )
                    if title_elem:
                        job["title"] = title_elem.inner_text().strip()

                    # Extract company name
                    company_elem = card.query_selector(".vNEEBe, .nJlQNd, .company")
                    if company_elem:
                        job["company"] = company_elem.inner_text().strip()

                    # Extract location
                    location_elem = card.query_selector(".Qk80Jf, .location, .vNEEBe")
                    if location_elem:
                        loc_text = location_elem.inner_text().strip()
                        # Google often combines company and location
                        if job.get("company") and job["company"] not in loc_text:
                            job["location"] = loc_text

                    # Extract via/source
                    via_elem = card.query_selector(".Kv0lAb, .via, .sMzDkb")
                    if via_elem:
                        job["via"] = via_elem.inner_text().strip().replace("via ", "")

                    # Extract date posted
                    date_elem = card.query_selector(".SuWscb, .date")
                    if date_elem:
                        job["date_posted"] = date_elem.inner_text().strip()

                    # Google Jobs doesn't directly provide URLs in the list view
                    # We'd need to click each job to get the apply URL
                    job["url"] = "https://www.google.com/search?q=" + quote_plus(
                        f"{job.get('title', '')} {job.get('company', '')} jobs"
                    )

                    # Only add job if we have at least title and company
                    if job.get("title") and job.get("company"):
                        job["source"] = "google"
                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error extracting Google job card: {e}")
                    continue

        except PlaywrightTimeout:
            logger.warning("Timeout waiting for Google Jobs to load")
        except Exception as e:
            logger.error(f"Error extracting Google jobs: {e}")

        return jobs

    # =========================================================================
    # Levels.fyi Methods
    # =========================================================================

    def _build_levelsfyi_url(
        self,
        search_term: str,
        location: str,
        days_ago: Optional[int] = None,
        job_type: Optional[str] = None,
        remote: bool = False,
    ) -> str:
        """Build Levels.fyi Jobs search URL with parameters."""
        base_url = "https://www.levels.fyi/jobs"
        params = []

        # Title/search term - Levels.fyi uses title parameter
        if search_term:
            # Convert search term to URL-friendly format
            title_slug = search_term.lower().replace(" ", "-")
            base_url = f"https://www.levels.fyi/jobs/title/{quote_plus(title_slug)}"

        # Location filter
        if location and location.lower() != "remote":
            params.append(f"location={quote_plus(location)}")

        # Remote filter
        if remote:
            params.append("workType=remote")

        # Date posted filter
        if days_ago:
            if days_ago <= 1:
                params.append("datePosted=today")
            elif days_ago <= 7:
                params.append("datePosted=week")
            elif days_ago <= 30:
                params.append("datePosted=month")

        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url

    def _extract_levelsfyi_jobs(self, page) -> list[dict]:
        """Extract job listings from Levels.fyi search results page."""
        jobs = []

        try:
            # Wait for job listings to load
            page.wait_for_selector(
                '[class*="JobCard"], [class*="jobCard"], a[href*="/jobs?jobId="]',
                timeout=15000,
            )

            # Scroll to load more jobs
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1000)")
                page.wait_for_timeout(500)

            # Get all job cards - Levels.fyi uses dynamic class names
            job_cards = page.query_selector_all(
                'a[href*="/jobs?jobId="], [class*="JobCard"], [class*="jobListItem"]'
            )

            for card in job_cards:
                try:
                    job = {}

                    # Extract job title - usually in a heading or strong element
                    title_elem = card.query_selector(
                        'h3, h4, [class*="jobTitle"], [class*="title"], strong'
                    )
                    if title_elem:
                        job["title"] = title_elem.inner_text().strip()

                    # Extract company name
                    company_elem = card.query_selector(
                        '[class*="company"], [class*="employer"], h2'
                    )
                    if company_elem:
                        job["company"] = company_elem.inner_text().strip()

                    # Extract location
                    location_elem = card.query_selector(
                        '[class*="location"], [class*="metadata"]'
                    )
                    if location_elem:
                        loc_text = location_elem.inner_text().strip()
                        # Parse out location from metadata
                        if "·" in loc_text:
                            parts = loc_text.split("·")
                            job["location"] = parts[0].strip()
                        else:
                            job["location"] = loc_text

                    # Extract job URL
                    href = card.get_attribute("href")
                    if not href:
                        link_elem = card.query_selector('a[href*="/jobs?jobId="]')
                        if link_elem:
                            href = link_elem.get_attribute("href")

                    if href:
                        if href.startswith("/"):
                            job["url"] = f"https://www.levels.fyi{href}"
                        else:
                            job["url"] = href

                        # Extract job ID
                        job_id_match = re.search(r"jobId=(\d+)", href)
                        if job_id_match:
                            job["job_id"] = job_id_match.group(1)

                    # Extract salary/compensation (Levels.fyi specialty!)
                    salary_elem = card.query_selector(
                        '[class*="salary"], [class*="comp"], [class*="compensation"]'
                    )
                    if salary_elem:
                        job["salary"] = salary_elem.inner_text().strip()
                    else:
                        # Try to find salary in the text content
                        card_text = card.inner_text()
                        salary_match = re.search(
                            r"\$[\d,]+K?\s*-?\s*\$?[\d,]*K?", card_text
                        )
                        if salary_match:
                            job["salary"] = salary_match.group(0).strip()

                    # Extract remote status
                    remote_elem = card.query_selector(
                        '[class*="remote"], [class*="workType"]'
                    )
                    if remote_elem:
                        remote_text = remote_elem.inner_text().strip().lower()
                        if "remote" in remote_text:
                            job["remote"] = True
                        elif "hybrid" in remote_text:
                            job["remote"] = "hybrid"

                    # Extract date posted
                    date_elem = card.query_selector(
                        '[class*="date"], [class*="posted"]'
                    )
                    if date_elem:
                        job["date_posted"] = date_elem.inner_text().strip()

                    # Only add job if we have at least title and company
                    if job.get("title") and job.get("company"):
                        job["source"] = "levelsfyi"
                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error extracting Levels.fyi job card: {e}")
                    continue

        except PlaywrightTimeout:
            logger.warning("Timeout waiting for Levels.fyi job cards to load")
        except Exception as e:
            logger.error(f"Error extracting Levels.fyi jobs: {e}")

        return jobs

    # =========================================================================
    # Indeed Methods
    # =========================================================================

    def _build_indeed_url(
        self,
        search_term: str,
        location: str,
        start: int = 0,
        days_ago: Optional[int] = None,
        job_type: Optional[str] = None,
        remote: bool = False,
    ) -> str:
        """Build Indeed search URL with parameters."""
        base_url = "https://www.indeed.com/jobs"
        params = [
            f"q={quote_plus(search_term)}",
            f"l={quote_plus(location)}",
            f"start={start}",
            "sort=date",
        ]

        if days_ago:
            params.append(f"fromage={days_ago}")

        if job_type:
            job_type_map = {
                "fulltime": "jt=fulltime",
                "parttime": "jt=parttime",
                "contract": "jt=contract",
                "internship": "jt=internship",
                "temporary": "jt=temporary",
            }
            if job_type.lower() in job_type_map:
                params.append(job_type_map[job_type.lower()])

        if remote:
            params.append("remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11")

        return f"{base_url}?{'&'.join(params)}"

    def _extract_indeed_jobs(self, page) -> list[dict]:
        """Extract job listings from Indeed search results page."""
        jobs = []

        try:
            page.wait_for_selector(
                '[data-testid="jobCard"], .job_seen_beacon, .jobsearch-ResultsList > li',
                timeout=10000,
            )

            job_cards = page.query_selector_all(
                '[data-testid="jobCard"], .job_seen_beacon, .resultContent'
            )

            for card in job_cards:
                try:
                    job = {}

                    title_elem = card.query_selector(
                        'h2.jobTitle a, h2.jobTitle span, [data-testid="jobTitle"], .jobTitle'
                    )
                    if title_elem:
                        job["title"] = title_elem.inner_text().strip()

                    company_elem = card.query_selector(
                        '[data-testid="company-name"], .companyName, .company'
                    )
                    if company_elem:
                        job["company"] = company_elem.inner_text().strip()

                    location_elem = card.query_selector(
                        '[data-testid="text-location"], .companyLocation, .location'
                    )
                    if location_elem:
                        job["location"] = location_elem.inner_text().strip()

                    link_elem = card.query_selector(
                        "h2.jobTitle a, a[data-jk], a.jcs-JobTitle"
                    )
                    if link_elem:
                        href = link_elem.get_attribute("href")
                        if href:
                            if href.startswith("/"):
                                job["url"] = f"https://www.indeed.com{href}"
                            else:
                                job["url"] = href

                            jk_match = re.search(r"jk=([a-f0-9]+)", href)
                            if jk_match:
                                job["job_key"] = jk_match.group(1)

                    salary_elem = card.query_selector(
                        '[data-testid="attribute_snippet_testid"], .salary-snippet, .salaryOnly'
                    )
                    if salary_elem:
                        job["salary"] = salary_elem.inner_text().strip()

                    snippet_elem = card.query_selector(
                        '.job-snippet, [data-testid="jobDescriptionText"], .underShelfFooter'
                    )
                    if snippet_elem:
                        job["snippet"] = snippet_elem.inner_text().strip()

                    date_elem = card.query_selector(
                        '.date, [data-testid="myJobsStateDate"], .visually-hidden'
                    )
                    if date_elem:
                        date_text = date_elem.inner_text().strip()
                        if any(
                            x in date_text.lower()
                            for x in ["posted", "ago", "just", "today"]
                        ):
                            job["date_posted"] = date_text

                    if job.get("title") and job.get("company"):
                        job["source"] = "indeed"
                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error extracting Indeed job card: {e}")
                    continue

        except PlaywrightTimeout:
            logger.warning("Timeout waiting for Indeed job cards to load")
        except Exception as e:
            logger.error(f"Error extracting Indeed jobs: {e}")

        return jobs

    # =========================================================================
    # Main Search Method
    # =========================================================================

    MIN_JOB_RATING = 0

    def find_jobs(
        self,
        search_term: str,
        location: str,
        results_wanted: int = 10,
        days_ago: Optional[int] = 7,
        job_type: Optional[str] = None,
        remote: bool = False,
        sites: Optional[list[str]] = None,
    ) -> str:
        """
        Search for job listings across multiple job boards.

        Use this tool to find job postings matching specific search terms and locations.
        Keep results_wanted to 10 or fewer to avoid rate limiting.

        Args:
            search_term: Job title or keywords to search for (e.g., "Python Developer", "Data Scientist")
            location: Location to search in (e.g., "Austin, TX", "Remote", "New York, NY")
            results_wanted: Number of job listings to return (default: 10, max recommended: 20)
            days_ago: Only show jobs posted within this many days (default: 7, use None for all)
            job_type: Filter by job type - "fulltime", "parttime", "contract", "internship", "temporary" (optional)
            remote: Filter for remote jobs only (default: False)
            sites: List of sites to search. Options: "linkedin", "glassdoor", "google", "levelsfyi", "indeed"
                   (default: ["linkedin"] - LinkedIn is the primary source)
                   Note: "levelsfyi" includes compensation data for most listings!

        Returns:
            JSON string containing a list of job objects with title, company, location, url, source, and other details.
        """
        # Default to LinkedIn as the primary source
        if sites is None:
            sites = ["linkedin"]

        # Validate sites
        valid_sites = [s.lower() for s in sites if s.lower() in self.SUPPORTED_SITES]
        if not valid_sites:
            logger.warning(
                f"No valid sites specified. Valid options: {self.SUPPORTED_SITES}"
            )
            valid_sites = ["linkedin"]

        logger.info(
            f"Searching for '{search_term}' jobs in '{location}' on {valid_sites} (max: {results_wanted})"
        )

        all_jobs = []
        jobs_per_site = max(results_wanted // len(valid_sites), 5)

        try:
            with Stealth().use_sync(sync_playwright()) as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ],
                )

                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )

                page = context.new_page()
                page.set_default_timeout(self.timeout)

                for site in valid_sites:
                    logger.info(f"Searching {site}...")
                    site_jobs = []

                    try:
                        if site == "linkedin":
                            site_jobs = self._search_linkedin(
                                page,
                                search_term,
                                location,
                                jobs_per_site,
                                days_ago,
                                job_type,
                                remote,
                            )
                        elif site == "glassdoor":
                            site_jobs = self._search_glassdoor(
                                page,
                                search_term,
                                location,
                                jobs_per_site,
                                days_ago,
                                job_type,
                                remote,
                            )
                        elif site == "google":
                            site_jobs = self._search_google(
                                page,
                                search_term,
                                location,
                                jobs_per_site,
                                days_ago,
                                job_type,
                                remote,
                            )
                        elif site == "levelsfyi":
                            site_jobs = self._search_levelsfyi(
                                page,
                                search_term,
                                location,
                                jobs_per_site,
                                days_ago,
                                job_type,
                                remote,
                            )
                        elif site == "indeed":
                            site_jobs = self._search_indeed(
                                page,
                                search_term,
                                location,
                                jobs_per_site,
                                days_ago,
                                job_type,
                                remote,
                            )

                        all_jobs.extend(site_jobs)
                        ##################################################
                        logger.info(f"Found {len(site_jobs)} jobs from {site}")

                        # Delay between sites
                        if len(valid_sites) > 1:
                            page.wait_for_timeout(2000)

                    except Exception as e:
                        logger.error(f"Error searching {site}: {e}")
                        continue

                browser.close()

        except Exception as e:
            logger.error(f"Browser error: {e}")
            return json.dumps({"error": str(e), "jobs": []})

        # Deduplicate by URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            url = job.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
                if len(unique_jobs) >= results_wanted:
                    break
        
        MIN_JOB_RATING = 0

        # Calculate ratings for unique jobs
        rated_jobs = []
        for job in unique_jobs:
            job["rating"] = self.calculate_rating(job)
            if job["rating"] >= MIN_JOB_RATING:
                rated_jobs.append(job)
            else:
                logger.info(f"Skipping job {job} (rating < {MIN_JOB_RATING})")
        
        unique_jobs = rated_jobs

        logger.info(f"Returning {len(unique_jobs)} unique jobs (filtered rating >= {MIN_JOB_RATING})")

        return json.dumps(
            {
                "search_term": search_term,
                "location": location,
                "sites_searched": valid_sites,
                "total_found": len(unique_jobs),
                "jobs": unique_jobs,
            },
            indent=2,
        )

    def _search_linkedin(
        self, page, search_term, location, max_jobs, days_ago, job_type, remote
    ) -> list[dict]:
        """Search LinkedIn and return jobs."""
        all_jobs = []
        jobs_per_page = 25

        pages_needed = (max_jobs + jobs_per_page - 1) // jobs_per_page

        for page_num in range(pages_needed):
            if len(all_jobs) >= max_jobs:
                break

            start = page_num * jobs_per_page
            url = self._build_linkedin_url(
                search_term, location, start, days_ago, job_type, remote
            )

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                # Check for auth wall
                if page.query_selector('[class*="authwall"], [data-test="authwall"]'):
                    logger.warning("LinkedIn auth wall detected")
                    break

                page_jobs = self._extract_linkedin_jobs(page)
                all_jobs.extend(page_jobs)

                if page_num < pages_needed - 1:
                    page.wait_for_timeout(2000)

            except Exception as e:
                logger.error(f"Error on LinkedIn page {page_num + 1}: {e}")
                continue

        return all_jobs[:max_jobs]

    def _search_glassdoor(
        self, page, search_term, location, max_jobs, days_ago, job_type, remote
    ) -> list[dict]:
        """Search Glassdoor and return jobs."""
        all_jobs = []

        url = self._build_glassdoor_url(
            search_term, location, 0, days_ago, job_type, remote
        )

        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            all_jobs = self._extract_glassdoor_jobs(page)

        except Exception as e:
            logger.error(f"Error searching Glassdoor: {e}")

        return all_jobs[:max_jobs]

    def _search_google(
        self, page, search_term, location, max_jobs, days_ago, job_type, remote
    ) -> list[dict]:
        """Search Google Jobs and return jobs."""
        all_jobs = []

        url = self._build_google_jobs_url(
            search_term, location, days_ago, job_type, remote
        )

        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            all_jobs = self._extract_google_jobs(page)

        except Exception as e:
            logger.error(f"Error searching Google Jobs: {e}")

        return all_jobs[:max_jobs]

    def _search_levelsfyi(
        self, page, search_term, location, max_jobs, days_ago, job_type, remote
    ) -> list[dict]:
        """Search Levels.fyi and return jobs with compensation data."""
        all_jobs = []

        url = self._build_levelsfyi_url(
            search_term, location, days_ago, job_type, remote
        )

        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            all_jobs = self._extract_levelsfyi_jobs(page)

        except Exception as e:
            logger.error(f"Error searching Levels.fyi: {e}")

        return all_jobs[:max_jobs]

    def _search_indeed(
        self, page, search_term, location, max_jobs, days_ago, job_type, remote
    ) -> list[dict]:
        """Search Indeed and return jobs."""
        all_jobs = []
        jobs_per_page = 15

        pages_needed = (max_jobs + jobs_per_page - 1) // jobs_per_page

        for page_num in range(pages_needed):
            if len(all_jobs) >= max_jobs:
                break

            start = page_num * jobs_per_page
            url = self._build_indeed_url(
                search_term, location, start, days_ago, job_type, remote
            )

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)

                # Check for CAPTCHA
                if page.query_selector('[id*="captcha"], [class*="captcha"]'):
                    logger.warning("Indeed CAPTCHA detected")
                    break

                page_jobs = self._extract_indeed_jobs(page)
                all_jobs.extend(page_jobs)

                if page_num < pages_needed - 1:
                    page.wait_for_timeout(1500)

            except Exception as e:
                logger.error(f"Error on Indeed page {page_num + 1}: {e}")
                continue

        return all_jobs[:max_jobs]
