import os
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from tools.google_sheets import GoogleSheetsTools
from tools.job_spy_tool import JobSpyTools
from tools.email_tools import EmailTools

# --- Config ---
# Ensure env vars: EMAIL_USER, EMAIL_APP_PASS
email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_APP_PASS")

# --- Init Tools ---
# 'spreadsheet_name' must match your Google Sheet name exactly
gs_tools = GoogleSheetsTools(credentials_path="credentials.json", spreadsheet_name="Job_Hunt_2025")
spy_tools = JobSpyTools()
comm_tools = EmailTools(email_address=email_user, app_password=email_pass)

# 1. Job Scout (Learning & Finding)
job_finder = Agent(
    name="Job Scout",
    role="Source Jobs",
    model=OpenAIChat(id="gpt-4o"),
    tools=[spy_tools, gs_tools],
    instructions=[
        "1. Call `get_user_preferences` to understand what to filter out.",
        "2. Call `find_jobs` with `results_wanted=20`.",
        "3. Filter results based on preferences.",
        "4. Call `add_job` for the best matches."
    ],
)

# 2. Resume Writer (Tailoring)
resume_writer = Agent(
    name="Resume Writer",
    role="Tailor Applications",
    model=OpenAIChat(id="gpt-4o"),
    tools=[gs_tools],
    instructions=[
        "Monitor 'Jobs' sheet for 'New' status.",
        "Create tailored resume content (simulated).",
        "Update 'Jobs' sheet notes with the tailored summary."
    ],
)

# 3. Comms Manager (Tracking & Sending)
comm_agent = Agent(
    name="Comms Manager",
    role="Manage Correspondence",
    model=OpenAIChat(id="gpt-4o"),
    tools=[comm_tools, gs_tools],
    instructions=[
        "SENDING APPLICATIONS:",
        "1. When instructed to apply, draft/send the email.",
        "2. CRITICAL: After sending, call `promote_to_application(job_url, 'Applied')`.",
        "   This moves the job to the 'Applications' tracking sheet.",

        "CHECKING INBOX:",
        "Search for keywords (Interview, LinkedIn).",
        "Update 'Applications' sheet status if a reply is found."
    ],
    markdown=True
)

# 4. Team Leader
headhunter_team = Team(
    name="Headhunter Manager",
    agents=[job_finder, resume_writer, comm_agent],
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You manage a job hunting agency.",
        "Coordinate the flow: Scout -> Writer -> Comms.",
        "Ensure Comms Manager uses the new `promote_to_application` tool when applications are sent."
    ]
)

if __name__ == "__main__":
    print("--- Starting Job Hunter v2.0 ---")
    headhunter_team.print_response(
        "Find 5 Python jobs in Austin, filter by my preferences, and apply to the best one.",
        stream=True
    )
