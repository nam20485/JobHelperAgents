from agno.os import AgentOS

from team import job_helper_team

# Create the AgentOS
agent_os = AgentOS(
    id="JobHelperAgentOS",
    teams=[job_helper_team],
)
app = agent_os.get_app()


if __name__ == "__main__":
    agent_os.serve(app="app:app", port=7777)
