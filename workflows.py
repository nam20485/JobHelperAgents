from agno.workflow import Workflow

import team

workflow = Workflow(
    name="Job Helper Workflow",
    steps=[
        team.job_finder_agent,
        team.resume_tailor_agent,
    ],
)
