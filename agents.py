from agno.agent import Agent

import models
from tools.google_sheets import GoogleSheetsTools
from tools.job_spy_tool import JobSpyTools


class JobHelperAgent(Agent):
    pass


JobHelperAgents_GoogleSheetsId = "1AZXQkRhtq_oDsCVoQqSOcK0ithQn13AYZaJdMRKI-WI"
# https://docs.google.com/spreadsheets/d/1AZXQkRhtq_oDsCVoQqSOcK0ithQn13AYZaJdMRKI-WI/edit?gid=1052401886#gid=1052401886


# Initialize Tools
gs_tools = GoogleSheetsTools(
    credentials_path="credentials.json", spreadsheet_id=JobHelperAgents_GoogleSheetsId
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
        "For each job found, check if it exists in the sheet (optional, if your sheet tool supports it).",
        "Add valid jobs to the Google Sheet using `add_job`.",
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
        "Check the Google Sheet for jobs with status 'New'.",
        "Update status to 'Tailored' after processing.",
    ],
    # db=SqliteDb(db_file="agent.db"),  # Store conversations
    add_history_to_context=True,  # Remember previous messages
    markdown=True,
)

# job_applicant_agent = JobHelperAgent(
#     model=models["openrouter_grok4_1_fast_model"],
#     tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
#     instructions=[
#         "You manage a job hunting agency.",
#         "Step 1: Ask the Scout to find jobs based on the user's query.",
#         "Step 2: Ask the Writer to process any new jobs found.",
#         "Always report back to the user with a summary of actions taken.",
#     ],
#     # db=SqliteDb(db_file="agent.db"),  # Store conversations
#     add_history_to_context=True,  # Remember previous messages
#     markdown=True,
# )
