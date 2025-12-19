from tools.google_sheets import GoogleSheetsTools
import time

def test_sheet_access():
    print("Testing Google Sheets Access...")
    gs = GoogleSheetsTools(
        credentials_path="credentials.json",
        spreadsheet_id="1AZXQkRhtq_oDsCVoQqSOcK0ithQn13AYZaJdMRKI-WI",
        resume_example_id="dummy",
        cover_letter_example_id="dummy"
    )
    
    # 1. Test check_job_exists
    test_url = f"https://example.com/test-job-{int(time.time())}"
    print(f"Checking for non-existent URL: {test_url}")
    exists = gs.check_job_exists(test_url)
    print(f"Exists? {exists}")
    
    # 2. Test add_job
    print("Adding test job...")
    result = gs.add_job(
        company="Test Company",
        role="Test Role",
        url=test_url,
        location="Remote",
        salary="$100k (Test)",
        source="debug_script",
        rating=5,
        notes="Automated test"
    )
    print(f"Add Job Result: {result}")
    
    # 3. Verify it exists now
    print("Verifying existence...")
    exists = gs.check_job_exists(test_url)
    print(f"Exists? {exists}")
    
    # 4. Test Read Doc (Use a dummy ID or a real known one)
    # This will likely fail without a real ID, but tests the method execution
    print("Testing Read Doc...")
    try:
        content = gs.read_google_doc("dummy_doc_id")
        print(f"Read Doc Result: {content}")
    except Exception as e:
        print(f"Read Doc Failed (Expected with dummy ID): {e}")
    
if __name__ == "__main__":
    test_sheet_access()
