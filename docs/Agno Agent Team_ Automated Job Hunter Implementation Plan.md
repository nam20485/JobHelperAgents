# **Agno Agent Team: Automated Job Hunter Implementation Plan**

## **1\. High-Level Architecture**

We will utilize **Agno's Team Architecture** in "Coordinate Mode". A central **Manager Agent** receives instructions from the AgentUI and delegates tasks to specialized sub-agents.

**The Workflow:**

1. **Manager:** Receives "Find Python jobs in Seattle" \-\> Delegates to **Job Finder**.  
2. **Job Finder:** Scrapes LinkedIn (via Apify) \-\> Saves to **Google Sheets**.  
3. **Manager:** Checks Sheets for new rows \-\> Delegates to **Resume Tailor**.  
4. **Resume Tailor:** Reads Master Resume \+ Job Desc \-\> Generates tailored PDF/DOCX \-\> Updates Sheet with link.  
5. **Manager:** Delegates to **Applicant** (Optional/Manual Trigger).  
6. **Applicant:** Navigates to Apply URL \-\> Fills fields \-\> Updates Sheet status to "Drafted".

## **2\. Agent Specifications & Tooling**

### **Agent A: job\_finder\_agent**

* **Goal:** Source jobs without getting IP-banned.  
* **Primary Tool:** **Apify** (Actor: linkedin-job-scraper or similar).  
  * *Why:* Handling proxies/rotating IPs is managed by Apify, preventing your local IP from being flagged.  
* **Storage Tool:** **GoogleSheetsTools** (Custom).  
  * *Why:* Acts as the "Database" but remains user-editable.  
* **Data Schema (Sheet Columns):**  
  * Date Found | Company | Role | URL | Status (New/Tailored/Applied) | Resume Link

### **Agent B: resume\_tailor\_agent**

* **Goal:** Optimize content for ATS (Applicant Tracking Systems).  
* **Input:** "Master Resume" (Markdown or PDF) \+ Job Description.  
* **Tools:**  
  * **File Tools:** To read the local master resume.  
  * **python-docx:** To programmatically swap text in a Word template (preserving formatting).  
* **Process:**  
  1. Agent reads Job Description.  
  2. Agent identifies keywords missing from Master Resume.  
  3. Agent rewrites "Summary" and "Experience" bullets.  
  4. Python Tool saves specific Job\_Company\_Date.docx.

### **Agent C: applicant\_agent**

* **Goal:** Automate the form-filling tedium.  
* **Tools:** **Browserbase** (or Selenium/Playwright via Agno Tools).  
* **Strategy:** "Draft Mode." The agent fills the application but does *not* click submit. It takes a screenshot for your review.

## **3\. Implementation: Custom Google Sheets Tool**

This is the custom Python class to allow your Agno agent to read/write to your tracking sheet.

### **Prerequisites**

1. Create a project in **Google Cloud Console**.  
2. Enable the **Google Sheets API** and **Google Drive API**.  
3. Create a **Service Account**, download the JSON key file (save as credentials.json).  
4. Share your target Google Sheet with the client\_email found in that JSON file.

### **tools/google\_sheets.py**

import json  
import gspread  
from agno.tools import Toolkit  
from agno.utils.log import logger  
from datetime import datetime

class GoogleSheetsTools(Toolkit):  
    def \_\_init\_\_(self, credentials\_path: str, spreadsheet\_name: str):  
        super().\_\_init\_\_(name="google\_sheets\_tools")  
        self.credentials\_path \= credentials\_path  
        self.spreadsheet\_name \= spreadsheet\_name  
        self.gc \= None  
        self.sh \= None  
        self.\_authenticate()  
          
        \# Register the tools the Agent can access  
        self.register\_ops(\[self.add\_job, self.get\_new\_jobs, self.update\_job\_status\])

    def \_authenticate(self):  
        """Internal helper to auth with Google"""  
        try:  
            self.gc \= gspread.service\_account(filename=self.credentials\_path)  
            self.sh \= self.gc.open(self.spreadsheet\_name)  
            logger.info(f"Successfully connected to Sheet: {self.spreadsheet\_name}")  
        except Exception as e:  
            logger.error(f"Failed to authenticate with Google Sheets: {e}")

    def add\_job(self, company: str, role: str, url: str, location: str \= "Remote"):  
        """  
        Adds a new job row to the Google Sheet.  
        Use this tool when you find a new job posting that matches criteria.  
        """  
        try:  
            worksheet \= self.sh.sheet1  
            date\_found \= datetime.now().strftime("%Y-%m-%d")  
              
            \# Check for duplicates (basic check on URL)  
            \# Warning: searching the whole sheet can be slow if large.  
            try:  
                cell \= worksheet.find(url)  
                if cell:  
                    return f"Job already exists in sheet at row {cell.row}"  
            except gspread.exceptions.CellNotFound:  
                pass \# This is good, it means it's new

            \# Assuming headers: Date, Company, Role, Location, URL, Status, Notes  
            worksheet.append\_row(\[date\_found, company, role, location, url, "New", ""\])  
            return f"Successfully added {role} at {company} to the sheet."  
        except Exception as e:  
            return f"Error adding job: {e}"

    def get\_new\_jobs(self):  
        """  
        Retrieves all jobs with status 'New'.  
        Use this to find jobs that need resume tailoring.  
        """  
        try:  
            worksheet \= self.sh.sheet1  
            all\_records \= worksheet.get\_all\_records()  
            new\_jobs \= \[job for job in all\_records if job.get('Status') \== 'New'\]  
            return json.dumps(new\_jobs)  
        except Exception as e:  
            return f"Error retrieving jobs: {e}"

    def update\_job\_status(self, url: str, new\_status: str, notes: str \= ""):  
        """  
        Updates the status of a job.  
        Use this after tailoring a resume (Status \-\> 'Tailored') or applying (Status \-\> 'Applied').  
        """  
        try:  
            worksheet \= self.sh.sheet1  
            try:  
                cell \= worksheet.find(url)  
            except gspread.exceptions.CellNotFound:  
                return "Job URL not found in sheet."  
              
            \# Update Status column (Assuming Status is Col 6, Notes is Col 7\)  
            \# Note: gspread uses 1-based indexing for columns  
            status\_col\_index \= 6   
            notes\_col\_index \= 7  
              
            worksheet.update\_cell(cell.row, status\_col\_index, new\_status)  
            if notes:  
                worksheet.update\_cell(cell.row, notes\_col\_index, notes)  
              
            return f"Updated job {url} to status: {new\_status}"  
        except Exception as e:  
            return f"Error updating status: {e}"

## **4\. Orchestrating the Team (team.py)**

This file ties the tools together using Agno's Team structure.

from agno.agent import Agent  
from agno.team import Team  
from agno.models.openai import OpenAIChat  
from tools.google\_sheets import GoogleSheetsTools  
\# from agno.tools.apify import ApifyTools \# Uncomment when Apify is set up

\# Initialize Shared Tools  
gs\_tools \= GoogleSheetsTools(credentials\_path="credentials.json", spreadsheet\_name="Job\_Hunt\_2025")

\# 1\. The Scout  
job\_finder \= Agent(  
    name="Job Scout",  
    role="Source Jobs",  
    model=OpenAIChat(id="gpt-4o"),  
    tools=\[gs\_tools\], \# Add ApifyTools() here  
    instructions=\[  
        "You are a fierce job hunter.",  
        "When asked to find jobs, use Apify to search LinkedIn.",  
        "Verify the job is not already in the database.",  
        "Use the \`add\_job\` tool to save findings to the Google Sheet."  
    \],  
    markdown=True  
)

\# 2\. The Writer  
resume\_writer \= Agent(  
    name="Resume Writer",  
    role="Tailor Applications",  
    model=OpenAIChat(id="gpt-4o"),  
    tools=\[gs\_tools\], \# Needs access to read 'New' jobs and update status  
    instructions=\[  
        "Check the Google Sheet for jobs with status 'New' using \`get\_new\_jobs\`.",  
        "For each job, analyze the description.",  
        "Update the sheet status to 'Tailored' after processing."  
        \# Add python-docx logic here later  
    \],  
    markdown=True  
)

\# 3\. The Manager  
headhunter\_team \= Team(  
    name="Headhunter Manager",  
    agents=\[job\_finder, resume\_writer\],  
    model=OpenAIChat(id="gpt-4o"),  
    instructions=\[  
        "You manage a job hunting agency.",  
        "Step 1: Ask the Scout to find jobs based on the user's query.",  
        "Step 2: Ask the Writer to process any new jobs found.",  
        "Always report back to the user with a summary of actions taken."  
    \]  
)

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Test run  
    headhunter\_team.print\_response("Find me 3 Senior Python Developer roles in Austin, TX", stream=True)

## **5\. Next Steps**

1. **Environment:** Set up a virtual environment (python \-m venv venv) and install requirements: pip install agno openai gspread apify-client.  
2. **Auth:** Get your Google Cloud Service Account JSON and place it in the root folder.  
3. **Run:** Execute python team.py to test the connection between the Scout and your Google Sheet.