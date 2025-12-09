from agno.team import Team

import models
from agents import job_finder_agent, resume_tailor_agent

job_helper_team = Team(
    name="Job Helper Team",
    members=[job_finder_agent, resume_tailor_agent],
    model=models.gpt_oss_model,
    instructions=[
        "You manage a job hunting agency.",
        "Step 1: Ask the Scout to find jobs based on the user's query.",
        "Step 2: Ask the Writer to process any new jobs found.",
        "Always report back to the user with a summary of actions taken.",
    ],
)
