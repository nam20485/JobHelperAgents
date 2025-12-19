from tools.google_sheets import GoogleSheetsTools
import time
import json

def test_sheet_access():
    print("Testing Google Sheets Access...")
    gs = GoogleSheetsTools(
        credentials_path="credentials.json",
        spreadsheet_id="1AZXQkRhtq_oDsCVoQqSOcK0ithQn13AYZaJdMRKI-WI",
        resume_example_id="dummy",
        cover_letter_example_id="dummy"
    )
     
    worksheet = gs._get_worksheet()
    if not worksheet:
        print("Failed to get worksheet")
        return

    # Check headers
    headers = worksheet.row_values(1)
    print(f"Current Headers: {headers}")

    # 1. Test check_job_exists
    test_url = f"https://example.com/debug-val-{int(time.time())}"
    print(f"Checking for non-existent URL: {test_url}")
    exists_json = gs.check_job_exists(test_url)
    exists_data = json.loads(exists_json)
    print(f"Exists? {exists_data.get('exists')}")
    
    # 2. Test add_job
    print(f"Adding debug validation job: {test_url}")
    result = gs.add_job(
        company="DEBUG_VAL_COMPANY",
        role="DEBUG_VAL_ROLE",
        url=test_url,
        location="DEBUG_VAL_LOCATION",
        salary="DEBUG_VAL_SALARY",
        source="debug_val_script",
        rating=99,
        notes="Validation run"
    )
    print(f"Add Job Result: {result}")
    
    # 3. Verify it exists and check column alignment
    print("Verifying existence and column alignment...")
    exists_json = gs.check_job_exists(test_url)
    exists_data = json.loads(exists_json)
    
    if exists_data.get("exists"):
        row = exists_data.get("row")
        raw_row = worksheet.row_values(row)
        print(f"Raw Row Data at {row}: {raw_row}")
        
        # Mapping verification
        # 0: Date, 1: Role, 2: Company, 3: Location, 4: URL, 5: Rating, 6: Status, 7: Source
        mapping = {
            "Date": raw_row[0] if len(raw_row) > 0 else "MISSING",
            "Role": raw_row[1] if len(raw_row) > 1 else "MISSING",
            "Company": raw_row[2] if len(raw_row) > 2 else "MISSING",
            "Location": raw_row[3] if len(raw_row) > 3 else "MISSING",
            "URL": raw_row[4] if len(raw_row) > 4 else "MISSING",
            "Rating": raw_row[5] if len(raw_row) > 5 else "MISSING",
            "Status": raw_row[6] if len(raw_row) > 6 else "MISSING",
            "Notes": raw_row[11] if len(raw_row) > 11 else "MISSING",
        }
        print("Mapped Data Check:")
        for k, v in mapping.items():
            print(f"  {k}: {v}")
            
        # 4. Test status update
        print("Testing Status Update to 'Tailoring'...")
        update_result = gs.update_job_status(test_url, "Tailoring", "Update test")
        print(f"Update Result: {update_result}")
        
        # Re-fetch raw row
        raw_row_updated = worksheet.row_values(row)
        print(f"Updated Status (should be in col 7): {raw_row_updated[6] if len(raw_row_updated) > 6 else 'MISSING'}")
        print(f"Updated Notes (should be in col 13): {raw_row_updated[12] if len(raw_row_updated) > 12 else 'MISSING'}")

    else:
        print("CRITICAL: Job was NOT found after adding.")
    
if __name__ == "__main__":
    test_sheet_access()
