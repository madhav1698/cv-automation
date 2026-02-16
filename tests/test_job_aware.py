"""
Test script to verify job-aware bullet replacement
"""
from update_cv import update_cv_bullets

# Test data with bullets grouped by job
test_bullets = {
    "PEERMUSIC – Data Analytics Developer": [
        "Built and maintained analytics-ready data models across bronze, silver, and gold layers, enabling consistent, attribution-style analysis on complex operational data.",
        "Standardized heterogeneous datasets by designing SQL transformations and entity mappings, reducing ambiguity and making data easier to consume and explain.",
        "Supported data ingestion workflows by inspecting incoming metadata structures, validating schemas, and enforcing column-level consistency, improving reliability of downstream models.",
        "Automated data preparation and validation using Python, accelerating delivery of usable datasets while reducing manual intervention.",
        "Translated ambiguous business requirements into transparent, well-documented data models, prioritizing correctness, usability, and long-term maintainability."
    ],
    "REPHRAIN, University of Bristol – Research Data Scientist": [
        "Designed unified data models integrating multiple structured and unstructured sources, enabling consistent analytics across complex datasets.",
        "Built Python-based data quality and validation tooling, reducing assessment time by 80% and increasing trust in transformed datasets.",
        "Worked closely with non-technical stakeholders to explain data transformations, assumptions, and limitations, ensuring correct interpretation and adoption.",
        "Delivered analytics outputs focused on clarity, traceability, and reproducibility, aligning data work with real user needs and governance requirements."
    ],
    "IBA GROUP – Data Scientist": [
        "Automated ETL pipelines using Python and SQL, consolidating data from multiple operational systems into a clean analytics layer.",
        "Modeled aviation datasets to support performance monitoring and anomaly detection, improving data accuracy by 75%.",
        "Partnered with business teams to translate operational needs into structured, decision-ready datasets and analytics outputs."
    ],
    "BRISTOL DIGITAL FUTURES INSTITUTE – Data Analyst": [
        "Cleaned, modeled, and analyzed multi-source telecom datasets, producing insights used directly by senior stakeholders.",
        "Built dashboards on top of well-structured analytical datasets, ensuring insights were explainable and reusable."
    ]
}

test_summary = (
    "Analytics engineer with 5+ years of progressive modeling analytics-ready data models and data transformation pipelines across "
    "complex, multi-source environments. Strong in SQL and Python, with hands-on experience standardizing heterogeneous datasets, "
    "enforcing schemas and metadata, and balancing correctness, usability, and long-term maintainability."
)

input_file = "Madhav_Manohar Gopal_CV .docx"
output_file = "outputs/test_job_aware_cv.docx"

print("Testing job-aware bullet replacement...")
print(f"Jobs to update: {list(test_bullets.keys())}")
print(f"Total bullets: {sum(len(bullets) for bullets in test_bullets.values())}")
print()

try:
    update_cv_bullets(
        input_file=input_file,
        output_file=output_file,
        custom_summary=test_summary,
        custom_bullets=test_bullets
    )
    print("\nTest completed successfully!")
    print(f"Check the output file: {output_file}")
except Exception as e:
    print(f"\nTest failed: {e}")
    import traceback
    traceback.print_exc()
