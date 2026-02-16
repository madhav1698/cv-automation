"""
Test script to verify flexible bullet counts
"""
from update_cv import update_cv_bullets

# Test with DIFFERENT numbers of bullets per job
# Template has: PEERMUSIC (6), REPHRAIN (6), IBA (6), BRISTOL (4)
# We'll provide: PEERMUSIC (3), REPHRAIN (7), IBA (5), BRISTOL (2)
test_bullets = {
    "PEERMUSIC – Data Analytics Developer": [
        "First bullet for Peermusic",
        "Second bullet for Peermusic",
        "Third bullet for Peermusic"
        # Only 3 bullets - should DELETE 3 old bullets from template
    ],
    "REPHRAIN, University of Bristol – Research Data Scientist": [
        "First bullet for REPHRAIN",
        "Second bullet for REPHRAIN",
        "Third bullet for REPHRAIN",
        "Fourth bullet for REPHRAIN",
        "Fifth bullet for REPHRAIN",
        "Sixth bullet for REPHRAIN",
        "Seventh bullet for REPHRAIN - THIS IS NEW!"
        # 7 bullets - should ADD 1 new bullet
    ],
    "IBA GROUP – Data Scientist": [
        "First bullet for IBA",
        "Second bullet for IBA",
        "Third bullet for IBA",
        "Fourth bullet for IBA",
        "Fifth bullet for IBA"
        # 5 bullets - should DELETE 1 old bullet
    ],
    "BRISTOL DIGITAL FUTURES INSTITUTE – Data Analyst": [
        "First bullet for Bristol",
        "Second bullet for Bristol"
        # 2 bullets - should DELETE 2 old bullets
    ]
}

test_summary = "Test summary for flexible bullet counts."

input_file = "Madhav_Manohar Gopal_CV .docx"
output_file = "outputs/test_flexible_bullets.docx"

print("Testing flexible bullet counts...")
print("Template bullets: PEERMUSIC (6), REPHRAIN (6), IBA (6), BRISTOL (4)")
print("Providing: PEERMUSIC (3), REPHRAIN (7), IBA (5), BRISTOL (2)")
print()

try:
    update_cv_bullets(
        input_file=input_file,
        output_file=output_file,
        custom_summary=test_summary,
        custom_bullets=test_bullets
    )
    print("\nTest completed!")
    print(f"Check the output: {output_file}")
    print("\nExpected: Replaced 17, Added 1, Removed 6")
except Exception as e:
    print(f"\nTest failed: {e}")
    import traceback
    traceback.print_exc()
