from agno.agent import Agent

import models
from tools.google_sheets import GoogleSheetsTools
from tools.job_spy_tool import JobSpyTools


class JobHelperAgent(Agent):
    pass


JobHelperAgents_GoogleSheetsId = "1AZXQkRhtq_oDsCVoQqSOcK0ithQn13AYZaJdMRKI-WI"
# https://docs.google.com/spreadsheets/d/1AZXQkRhtq_oDsCVoQqSOcK0ithQn13AYZaJdMRKI-WI/edit?gid=1052401886#gid=1052401886

ResumeExample_GoogleDocsId = "1bLST1EhpajDO3Ft2w_FV2kZkZ3r7QROM2VPVB-_DOQ8"
CoverLetterExample_GoogleDocsId = "1SY9R1BRZrpGnCcbNs9qx4dxTtAW9BveHehJ8ylngW74"


# Initialize Tools
gs_tools = GoogleSheetsTools(
    credentials_path="credentials.json",
    spreadsheet_id=JobHelperAgents_GoogleSheetsId,
    resume_example_id=ResumeExample_GoogleDocsId,
    cover_letter_example_id=CoverLetterExample_GoogleDocsId,
)
spy_tools = JobSpyTools()


job_finder_agent = JobHelperAgent(
    name="Job Finder",
    role="Source Jobs",
    model=models.glm_4_5_air_model,
    tools=[
        spy_tools,
        gs_tools,
    ],
    instructions=[
        "Use `find_jobs` to search for roles. Keep `results_wanted` to 10 to avoid rate limits.",
        "For each job found, check if it exists in the sheet using `check_job_exists`.",
        "Add valid jobs to the Google Sheet using `add_job`. Ensure you pass the `rating` from the found job.",
    ],
    # db=SqliteDb(db_file="agent.db"),  # Store conversations
    add_history_to_context=True,  # Remember previous messages
    markdown=True,
)

resume_tailor_agent = JobHelperAgent(
    name="Targetted Resume and Cover Letter Writer",
    model=models.glm_4_5_air_model,
    tools=[gs_tools],
    instructions=[
        "Use `get_new_jobs` to find jobs with status 'Found' or 'New'.",
        "Update status to 'Tailoring' when you begin processing.",
        "Update status to 'Tailored' when you finish processing.",
    ],
    # db=SqliteDb(db_file="agent.db"),  # Store conversations
    add_history_to_context=True,  # Remember previous messages
    markdown=True,
)

job_applicant_agent = JobHelperAgent(
    model=models.gemini_2_5_flash_model,
    tools=[gs_tools],
    instructions=[
        "You orchestrate a team of agents to find and process job applications.",
        "Step 1: Ask the Job Finder to find jobs based on the user's query.",
        "Step 2: Ask the Tailor to process any new jobs found.",
        "Always report back to the user with a summary of actions taken.",
    ],
    # db=SqliteDb(db_file="agent.db"),  # Store conversations
    add_history_to_context=True,  # Remember previous messages
    markdown=True,
)
