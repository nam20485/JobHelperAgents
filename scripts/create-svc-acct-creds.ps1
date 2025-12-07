<#
.SYNOPSIS
    Automates the creation of a Google Cloud Service Account and credentials for the Agno Job Hunter.
.DESCRIPTION
    This script will:
    1. Enable Google Sheets and Google Drive APIs.
    2. Create a specific Service Account for the agent.
    3. Generate and download the 'credentials.json' key file.
    4. Output the email address you need to share your Google Sheet with.
.NOTES
    Prerequisites:
    - Google Cloud SDK (gcloud) installed.
    - User must be logged in (gcloud auth login).
    - A Google Cloud Project must already exist.
#>

$ErrorActionPreference = "Stop"

function Check-Gcloud {
    if (-not (Get-Command "gcloud" -ErrorAction SilentlyContinue)) {
        Write-Error "The 'gcloud' CLI is not installed or not in your PATH. Please install the Google Cloud SDK first."
        exit 1
    }
}

function Get-ProjectID {
    $currentProject = gcloud config get-value project 2>$null
    if ([string]::IsNullOrWhiteSpace($currentProject)) {
        $inputProject = Read-Host "Enter your Google Cloud Project ID"
        if ([string]::IsNullOrWhiteSpace($inputProject)) {
            Write-Error "Project ID is required."
            exit 1
        }
        return $inputProject
    }
    Write-Host "Using current project: $currentProject" -ForegroundColor Cyan
    return $currentProject
}

# --- Main Script ---

Check-Gcloud

Write-Host "`n=== Agno Job Hunter GCP Setup ===`n" -ForegroundColor Cyan

# 1. Setup Project Context
$ProjectID = Get-ProjectID
$ServiceAccountName = "job-hunter-agent"
$ServiceAccountEmail = "$ServiceAccountName@$ProjectID.iam.gserviceaccount.com"
$KeyFileName = "credentials.json"

# 2. Enable APIs
Write-Host "Step 1: Enabling Google Sheets and Drive APIs..." -ForegroundColor Yellow
try {
    gcloud services enable sheets.googleapis.com drive.googleapis.com --project $ProjectID
    Write-Host "APIs enabled successfully." -ForegroundColor Green
}
catch {
    Write-Error "Failed to enable APIs. Ensure billing is enabled for project '$ProjectID'."
    exit 1
}

# 3. Create Service Account
Write-Host "`nStep 2: Checking/Creating Service Account ($ServiceAccountName)..." -ForegroundColor Yellow
$saExists = gcloud iam service-accounts list --project $ProjectID --filter="email:$ServiceAccountEmail" --format="value(email)"
if ($saExists) {
    Write-Host "Service account '$ServiceAccountName' already exists. Skipping creation." -ForegroundColor Gray
}
else {
    try {
        gcloud iam service-accounts create $ServiceAccountName `
            --description="Agent for Agno Job Hunter Team" `
            --display-name="Agno Job Hunter Agent" `
            --project $ProjectID
        Write-Host "Service account created." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to create service account."
        exit 1
    }
}

# 4. Create and Download Key
Write-Host "`nStep 3: Creating/Downloading key file..." -ForegroundColor Yellow
if (Test-Path $KeyFileName) {
    Write-Warning "A file named '$KeyFileName' already exists in this folder."
    $overwrite = Read-Host "Overwrite it? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Host "Skipping key creation." -ForegroundColor Gray
    } else {
        Remove-Item $KeyFileName -Force
        gcloud iam service-accounts keys create $KeyFileName `
            --iam-account $ServiceAccountEmail `
            --project $ProjectID
    }
}
else {
    try {
        gcloud iam service-accounts keys create $KeyFileName `
            --iam-account $ServiceAccountEmail `
            --project $ProjectID
        Write-Host "Key saved to '$KeyFileName'." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to create key file."
        exit 1
    }
}

# 5. Final Instructions
Write-Host "`n=== Setup Complete! ===" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
Write-Host "ACTION REQUIRED:" -ForegroundColor Yellow
Write-Host "1. Open your Google Sheet in your browser."
Write-Host "2. Click the 'Share' button."
Write-Host "3. Paste this email address into the share box:"
Write-Host "   $ServiceAccountEmail" -ForegroundColor Magenta
Write-Host "4. Grant it 'Editor' access."
Write-Host "------------------------------------------------------------"
