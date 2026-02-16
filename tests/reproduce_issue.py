
import re

JOB_TITLES = [
    "PEERMUSIC – Data Analytics Developer",
    "REPHRAIN, University of Bristol – Research Data Scientist",
    "IBA GROUP – Data Scientist",
    "BRISTOL DIGITAL FUTURES INSTITUTE – Data Analyst"
]

def original_match_logic(line, job_titles):
    line_upper = line.upper()
    for job_title in job_titles:
        job_upper = job_title.upper()
        if line_upper == job_upper:
            return job_title
        
        # Check if line contains key parts of job title
        job_parts = job_title.split("–")
        if len(job_parts) >= 2:
            company_part = job_parts[0].strip().upper()
            if company_part in line_upper and ("–" in line or "-" in line or "—" in line):
                if not any(line.strip().startswith(char) for char in ['•', '-', '*', '▪']):
                    return job_title
        
        # Also try matching just the company name (first word before dash)
        # Fix: Line 264 in cv_generator_gui.py: job_title.split("–")[0].split(",")[0].strip().upper()
        company_name_only = job_title.split("–")[0].split(",")[0].strip().upper()
        if company_name_only and company_name_only in line_upper:
            if len(line.split()) <= 8 and ("–" in line or "-" in line or "—" in line):
                return job_title
    return None

test_cases = [
    "REPHRAIN - University of Bristol - Data Scientist",
    "REPHRAIN | University of Bristol | Data Scientist",
    "REPHRAIN : University of Bristol : Data Scientist",
    "rephrain - univ of brtostol | Data scientist",
]

print("Testing original logic:")
for tc in test_cases:
    match = original_match_logic(tc, JOB_TITLES)
    print(f"'{tc}' -> {match}")
