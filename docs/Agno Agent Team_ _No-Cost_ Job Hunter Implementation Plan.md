# **Agno Agent Team: "No-Cost" Job Hunter Implementation Plan**

## **1\. High-Level Architecture**

We are replacing the paid cloud scraper (Apify) with a local open-source scraper (**JobSpy**).

**The Workflow:**

1. **Manager:** Receives "Find Python jobs in Austin" \-\> Delegates to **Job Finder**.  
2. **Job Finder:** Runs JobSpy locally to scrape LinkedIn, Indeed, and Glassdoor \-\> Saves to **Google Sheets**.  
3. **Manager:** Checks Sheets for new rows \-\> Delegates to **Resume Tailor**.  
4. **Resume Tailor:** Reads Master Resume \+ Job Desc \-\> Generates tailored PDF/DOCX \-\> Updates Sheet.  
5. **Applicant:** (Manual/Semi-Auto) User clicks the link in the sheet to apply.

## **2\. Agent Specifications & Tooling**

### **Agent A: job\_finder\_agent**

* **Goal:** Find jobs using free, open-source tools.  
* **Primary Tool:** **JobSpyTools** (Custom wrapper for python-jobspy).  
  * *Pros:* Free, supports multiple sites (LinkedIn, Indeed, ZipRecruiter, Glassdoor).  
  * *Cons:* Runs on your local IP. **Rate Limit Warning:** Search for 10-20 jobs at a time, not hundreds.  
* **Storage Tool:** **GoogleSheetsTools** (Same as before).

### **Agent B: resume\_tailor\_agent**

* **Goal:** Tailor resume content.  
* **Cost Check:** This agent uses an LLM (OpenAI/Anthropic). To keep this "Low Cost," ensure you prompt efficiently or use a cheaper model like gpt-4o-mini for the bulk of the text generation.

## **3\. Implementation: Free Job Scraper Tool**

This custom tool wraps the jobspy library to format data exactly how our Google Sheet expects it.

### **Prerequisites**

1. Install the library: pip install python-jobspy pandas

### **tools/job\_spy\_tool.py**

from agno.tools import Toolkit  
from agno.utils.log import logger  
import pandas as pd  
from jobspy import scrape\_jobs

class JobSpyTools(Toolkit):  
    def \_\_init\_\_(self):  
        super().\_\_init\_\_(name="job\_spy\_tools")  
        self.register\_ops(\[self.find\_jobs\])

    def find\_jobs(self, search\_term: str, location: str \= "Remote", results\_wanted: int \= 10):  
        """  
        Searches for jobs on LinkedIn, Indeed, and Glassdoor using JobSpy.  
          
        :param search\_term: The job title or keywords (e.g., "Python Developer")  
        :param location: The location (e.g., "Austin, TX", "Remote")  
        :param results\_wanted: Max number of jobs to fetch (Keep this under 20 to be safe)  
        :return: A list of found jobs as dictionaries.  
        """  
        logger.info(f"Searching for {results\_wanted} '{search\_term}' jobs in {location}...")  
          
        try:  
            \# Scrape jobs from multiple free sources  
            jobs\_df \= scrape\_jobs(  
                site\_name=\["linkedin", "indeed", "glassdoor"\],  
                search\_term=search\_term,  
                location=location,  
                results\_wanted=results\_wanted,  
                country\_watchlist=\["US"\], \# Change if you are outside the US  
                hours\_old=72 \# Only fresh jobs from the last 3 days  
            )

            if jobs\_df.empty:  
                return "No jobs found. Try broadening your search terms."

            \# Normalize data for our Google Sheet  
            \# JobSpy columns: id, site, job\_url, job\_url\_direct, title, company, location, date\_posted, etc.  
            formatted\_jobs \= \[\]  
            for \_, row in jobs\_df.iterrows():  
                formatted\_jobs.append({  
                    "Company": row.get('company'),  
                    "Role": row.get('title'),  
                    "Location": row.get('location'),  
                    "URL": row.get('job\_url'),  
                    "Site": row.get('site')  
                })  
              
            return formatted\_jobs

        except Exception as e:  
            logger.error(f"JobSpy failed: {e}")  
            return f"Error during job search: {e}"

## **4\. Orchestrating the Free Team (team.py)**

This file ties the free tools together.

from agno.agent import Agent  
from agno.team import Team  
from agno.models.openai import OpenAIChat  
from tools.google\_sheets import GoogleSheetsTools  
from tools.job\_spy\_tool import JobSpyTools

\# Initialize Tools  
gs\_tools \= GoogleSheetsTools(credentials\_path="credentials.json", spreadsheet\_name="Job\_Hunt\_2025")  
spy\_tools \= JobSpyTools()

\# 1\. The Free Scout  
job\_finder \= Agent(  
    name="Free Job Scout",  
    role="Source Jobs",  
    model=OpenAIChat(id="gpt-4o-mini"), \# Using Mini to save costs  
    tools=\[spy\_tools, gs\_tools\],   
    instructions=\[  
        "Use \`find\_jobs\` to search for roles. Keep \`results\_wanted\` to 10 to avoid rate limits.",  
        "For each job found, check if it exists in the sheet (optional, if your sheet tool supports it).",  
        "Add valid jobs to the Google Sheet using \`add\_job\`."  
    \],  
    markdown=True  
)

\# 2\. The Writer (unchanged)  
resume\_writer \= Agent(  
    name="Resume Writer",  
    role="Tailor Applications",  
    model=OpenAIChat(id="gpt-4o"), \# Keep standard 4o for better writing quality  
    tools=\[gs\_tools\],  
    instructions=\[  
        "Check the Google Sheet for jobs with status 'New'.",  
        "Update status to 'Tailored' after processing."  
    \],  
    markdown=True  
)

\# 3\. The Team Leader  
headhunter\_team \= Team(  
    name="Headhunter Manager",  
    agents=\[job\_finder, resume\_writer\],  
    model=OpenAIChat(id="gpt-4o"),  
    instructions=\[  
        "You manage a 'Zero Cost' job hunting agency.",  
        "Delegate searching to the Job Scout first.",  
        "Then delegate tailoring to the Resume Writer.",  
        "Report back to the user."  
    \]  
)

if \_\_name\_\_ \== "\_\_main\_\_":  
    headhunter\_team.print\_response("Find 5 Junior DevOps jobs in Seattle", stream=True)  
