import sys
import json
import os
from .analyzer import TemplateAnalyzer
from .learner import TemplateLearner

def main():
    if "--gui" in sys.argv:
        from .gui import TemplateIntelligenceUI
        app = TemplateIntelligenceUI()
        app.mainloop()
        return

    if len(sys.argv) < 2:
        print("Usage: python -m template_intelligence.main <path_to_docx>")
        return

    docx_path = sys.argv[1]
    if not os.path.exists(docx_path):
        print(f"Error: File not found {docx_path}")
        return

    print(f"--- Analyzing: {os.path.basename(docx_path)} ---")
    analyzer = TemplateAnalyzer(docx_path)
    analysis = analyzer.analyze()
    
    # Save Analysis Results
    analysis_path = "analysis.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        f.write(analysis.model_dump_json(indent=4))
    print(f"1. Analysis saved to {analysis_path}")

    # Learning Phase
    print("--- Learning Pattern from Analysis ---")
    learner = TemplateLearner(analysis, docx_path)
    try:
        config = learner.learn()
        config_path = "template_config.json"
        learner.save_config(config, config_path)
        print(f"2. Learning Success! Config saved to {config_path}")
        print(f"\n--- [DETECTED EXPERIENCE BLOCKS] ---")
        for i, block in enumerate(analysis.inferred_experience_blocks):
            print(f"Block #{i+1}:")
            if block.company_idx is not None:
                print(f"  Company:  {analysis.paragraphs[block.company_idx].text}")
            if block.role_idx is not None:
                print(f"  Role:     {analysis.paragraphs[block.role_idx].text}")
            if block.location_idx is not None:
                print(f"  Location: {analysis.paragraphs[block.location_idx].text}")
            if block.date_idx is not None:
                print(f"  Dates:    {analysis.paragraphs[block.date_idx].text}")
            if block.bullet_start_idx is not None and block.bullet_end_idx is not None:
                bullet_count = block.bullet_end_idx - block.bullet_start_idx + 1
                print(f"  Bullets: Found {bullet_count} bullets")
            print("-" * 30)
            
        print(f"\nSection Info: Experience found from paragraph {config.experience_section['start']} to {config.experience_section['end']}")
    except Exception as e:
        print(f"Error during learning: {e}")

if __name__ == "__main__":
    main()
