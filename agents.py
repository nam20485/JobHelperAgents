import os

from agno.agent import Agent
from agno.team import Team

# from agno.db.sqlite import SqliteDb
# from agno.tools.mcp import MCPTools
from models import models
from tools.google_sheets import GoogleSheetsTools
from tools.job_spy_tool import JobSpyTools


class JobHelperAgent(Agent):
    pass


# Initialize Tools
gs_tools = GoogleSheetsTools(
    credentials_path="credentials.json", spreadsheet_name="Job_Hunt_2025"
)
spy_tools = JobSpyTools()


job_finder_agent = JobHelperAgent(
    name="Job Finder",
    role="Source Jobs",
    model=models["openrouter_grok4_1_fast"],
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
    model=models["openrouter_grok4_1_fast"],
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

job_helper_team = Team(
    name="Job Helper Team",
    members=[job_finder_agent, resume_tailor_agent],
    model=models["openrouter_grok4_1_fast"],
    instructions=[
        "You manage a job hunting agency.",
        "Step 1: Ask the Scout to find jobs based on the user's query.",
        "Step 2: Ask the Writer to process any new jobs found.",
        "Always report back to the user with a summary of actions taken.",
    ],
)

if __name__ == "__main__":
    # Test run
    job_helper_team.print_response(
        "Find me 3 Senior Python Developer roles in Austin, TX", stream=True
    )
