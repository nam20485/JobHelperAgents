from agno.team import Team

import models
from agents import job_finder_agent, resume_tailor_agent

job_helper_team = Team(
    name="Job Helper Team",
    members=[job_finder_agent, resume_tailor_agent],
    model=models.glm_4_5_air_model,
    instructions=[
        "You orchestrate a team of agents to find and process job applications.",
        "Step 1: Ask the Job Finder to find jobs based on the user's query.",
        "Step 2: Ask the Tailor to process any new jobs found.",
        "Always report back to the user with a summary of actions taken.",
    ],
)
