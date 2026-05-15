
import re

JOB_TITLES = [
    "PEERMUSIC – Data Analytics Developer",
    "REPHRAIN, University of Bristol – Research Data Scientist",
    "IBA GROUP – Data Scientist",
    "BRISTOL DIGITAL FUTURES INSTITUTE – Data Analyst"
]

def flexible_match_logic(line, job_titles):
    line = line.strip()
    if not line:
        return None
        
    line_upper = line.upper()
    
    for job_title in job_titles:
        job_upper = job_title.upper()
        
        # Exact match (case insensitive)
        if line_upper == job_upper:
            return job_title
            
        # Check if line contains key parts of job title
        job_parts = job_title.split("–")
        if len(job_parts) >= 2:
            company_part = job_parts[0].strip().upper()
            
            # Check if line contains company name and a common delimiter
            has_delimiter = any(d in line for d in ["–", "-", "—", "|", ":", "/"])
            
            if company_part in line_upper and has_delimiter:
                # Also check if it's not just a bullet point
                if not any(line.strip().startswith(char) for char in ['•', '-', '*', '▪']):
                    return job_title
        
        # Also try matching just the company name
        company_name_only = job_title.split("–")[0].split(",")[0].strip().upper()
        if company_name_only and company_name_only in line_upper:
            # Make sure it's not just a partial match in a bullet
            has_delimiter = any(d in line for d in ["–", "-", "—", "|", ":", "/"])
            if len(line.split()) <= 10 and (has_delimiter or len(line) < 100):
                return job_title
                
    return None

test_cases = [
    "REPHRAIN - University of Bristol - Data Scientist",
    "REPHRAIN | University of Bristol | Data Scientist",
    "REPHRAIN : University of Bristol : Data Scientist",
    "rephrain - univ of brtostol | Data scientist",
    "IBA GROUP | Junior Scientist",
    "PEERMUSIC : analytics",
    "univ of brtostol / rephrain - data scientist"
]

print("Testing flexible logic:")
for tc in test_cases:
    match = flexible_match_logic(tc, JOB_TITLES)
    print(f"'{tc}' -> {match}")
