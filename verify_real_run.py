from tools.google_sheets import GoogleSheetsTools
import json

def verify():
    gs = GoogleSheetsTools(
        credentials_path="credentials.json",
        spreadsheet_id="1AZXQkRhtq_oDsCVoQqSOcK0ithQn13AYZaJdMRKI-WI",
        resume_example_id="dummy",
        cover_letter_example_id="dummy"
    )
    
    print("Fetching last 5 jobs from sheet...")
    worksheet = gs._get_worksheet()
    all_records = worksheet.get_all_records()
    last_5 = all_records[-5:] if all_records else []
    
    print(f"Total jobs: {len(all_records)}")
    for i, job in enumerate(last_5):
        print(f"Job {len(all_records)-5+i+1}: {job.get('Company')} - {job.get('Role')} - Status: {job.get('Status')}")
        print(f"  Notes: {job.get('Notes')}")

if __name__ == "__main__":
    verify()
