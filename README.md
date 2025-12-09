# JobHelperAgents

An automated job hunting system powered by AI agents that finds job postings, tracks them in Google Sheets, and helps tailor resumes and cover letters for each position.

## 🚀 Features

- **Automated Job Search**: Searches multiple job boards (LinkedIn, Glassdoor, Google Jobs, Indeed, Levels.fyi) for relevant positions
- **Google Sheets Integration**: Automatically tracks all found jobs in a centralized spreadsheet
- **Multi-Agent Team**: Coordinated AI agents working together to streamline your job search
- **Resume Tailoring**: AI-powered resume and cover letter customization for each job posting
- **Duplicate Detection**: Prevents adding the same job twice to your tracking sheet
- **Status Management**: Track job application progress from discovery to offer

## 📋 Prerequisites

- Python 3.12 or higher
- Google Cloud Service Account with Google Sheets API enabled
- API keys for AI models (Gemini, OpenRouter - optional)
- Playwright browsers installed

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd JobHelperAgents
```

2. Install dependencies using `uv` (recommended) or `pip`:
```bash
# Using uv
uv sync

# Or using pip
pip install -e .
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Set up Google Sheets API:
   - Create a Google Cloud project
   - Enable Google Sheets API
   - Create a service account and download the credentials JSON
   - Save the credentials as `credentials.json` in the project root
   - Create a Google Sheet and share it with your service account email
   - Copy the Sheet ID from the URL

5. Configure environment variables:
```bash
# Optional: For OpenRouter models
export OPENROUTER_AGNO_API_KEY=your_api_key_here
```

6. Update the spreadsheet ID in `agents.py`:
```python
JobHelperAgents_GoogleSheetsId = "your-google-sheet-id-here"
```

## 🎯 Usage

### Running the Job Helper Team

```python
from team import job_helper_team

# Find and track jobs
job_helper_team.print_response(
    "Find me 5 Senior Python Developer roles in Austin, TX",
    stream=True
)
```

### Individual Agents

#### Job Finder Agent
Searches job boards and adds results to Google Sheets:

```python
from agents import job_finder_agent

job_finder_agent.print_response(
    "Search for Data Scientist positions in San Francisco"
)
```

#### Resume Tailor Agent
Processes new jobs and helps customize application materials:

```python
from agents import resume_tailor_agent

resume_tailor_agent.print_response(
    "Review new jobs and suggest resume improvements"
)
```

## 📊 Google Sheets Structure

The tracking sheet includes the following columns:

| Column | Description |
|--------|-------------|
| Date | Date the job was found |
| Company | Company name |
| Role | Job title/position |
| Location | Job location (Remote, City, etc.) |
| URL | Link to job posting |
| Status | Current application status |
| Notes | Additional notes and timestamps |
| Source | Where the job was found (linkedin, glassdoor, etc.) |

### Status Values

- **New**: Just added, not yet processed
- **Tailored**: Resume has been customized
- **Applied**: Application submitted
- **Interview**: Interview scheduled/completed
- **Rejected**: Application rejected
- **Offer**: Received an offer
- **Declined**: Declined to apply or declined offer

## 🔧 Configuration

### Supported Job Sites

- LinkedIn (primary source)
- Glassdoor
- Google Jobs
- Indeed
- Levels.fyi (includes compensation data!)

### AI Models

The project uses multiple AI models configured in `models.py`:

- **Gemini 2.5 Flash**: Default model for agents (fast and cost-effective)
- **Gemini 3 Pro**: Advanced model option
- **OpenRouter (Grok)**: Alternative model (requires API key)

### Search Parameters

When using the job finder, you can customize:

- `results_wanted`: Number of results (default: 10, keep low to avoid rate limits)
- `days_ago`: Only show jobs posted within X days (default: 7)
- `job_type`: Filter by "fulltime", "parttime", "contract", "internship", "temporary"
- `remote`: Filter for remote jobs only
- `sites`: List of job boards to search

## 📁 Project Structure

```
JobHelperAgents/
├── agents.py              # Agent definitions (Job Finder, Resume Tailor)
├── team.py               # Team coordination logic
├── models.py             # AI model configurations
├── main.py               # Entry point
├── credentials.json      # Google Sheets credentials (not in repo)
├── tools/
│   ├── google_sheets.py  # Google Sheets integration
│   └── job_spy_tool.py   # Job search across multiple sites
├── docs/                 # Planning and documentation
└── README.md            # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

[Add your license here]

## 🐛 Troubleshooting

### Authentication Issues
- Ensure `credentials.json` is in the project root
- Verify the Google Sheet is shared with your service account email
- Check that Google Sheets API is enabled in your Google Cloud project

### Rate Limiting
- Keep `results_wanted` at 10 or lower
- Add delays between searches
- Use specific site selections rather than searching all sites

### Browser Issues
- Run `playwright install chromium` to ensure browsers are installed
- Check that you have sufficient disk space for browser downloads

## 📚 Dependencies

Key dependencies include:

- **agno**: AI agent framework (v2.3.4+)
- **playwright**: Browser automation for job scraping
- **gspread**: Google Sheets API integration
- **jobspy**: Job search functionality
- **fastapi**: Web framework (for future API features)
- **pandas**: Data manipulation

See `pyproject.toml` for the complete list.

## 🎓 Learn More

- [Agno Documentation](https://docs.agno.com/)
- [Google Sheets API Guide](https://developers.google.com/sheets/api)
- [Playwright Documentation](https://playwright.dev/python/)

---

Built with ❤️ using AI agents to make job hunting less painful.