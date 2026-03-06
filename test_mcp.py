#!/usr/bin/env python3
"""
Quick test script for MCP server functionality.

This script tests the MCP server tools locally without needing Claude Desktop.
Run this to verify everything works before setting up the MCP integration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import (
    grade_call_transcript,
    analyze_call_summary,
    get_scoring_rubric,
)


# Sample call transcript for testing
SAMPLE_TRANSCRIPT = """
Agent: Thank you for calling ABC Tech Support. This is Sarah speaking. How may I help you today?

Customer: Hi Sarah, I'm having trouble with my internet connection. It's been down for about 3 hours now.

Agent: I'm sorry to hear you're experiencing internet connectivity issues. I understand how frustrating that can be. Let me help you get that resolved right away. May I please have your account number or the phone number associated with your account?

Customer: Sure, it's 555-123-4567.

Agent: Thank you. Let me pull up your account... Okay, I see you're a valued customer with us for 2 years. I appreciate your patience. I'm going to run a diagnostic test on your modem. Can you tell me if you see any lights on your modem?

Customer: Yes, there are some red lights blinking.

Agent: That indicates the modem may need to be reset. I'm going to walk you through a quick reset process. First, please unplug the power cord from the back of the modem.

Customer: Okay, done.

Agent: Great. Now wait about 30 seconds, then plug it back in. Let me know when you see the lights start coming back on.

Customer: Alright... the lights are coming back on now. Some are green, some are still orange.

Agent: Perfect. The orange lights should turn green in about 2-3 minutes as the modem reconnects. While we wait, I want to mention that I see your current internet plan. Would you like me to check if there are any promotions available that might give you faster speeds at a better rate?

Customer: Actually, yes, that would be great.

Agent: Wonderful. I'll make a note to have our promotions team reach out to you within 24 hours. Now, can you try accessing a website to see if your internet is working?

Customer: Let me check... Yes! It's working now. Thank you so much!

Agent: That's excellent news! I'm so glad we could get that resolved for you. Is there anything else I can help you with today?

Customer: No, that was it. You've been very helpful.

Agent: It's been my pleasure assisting you today. You should expect a call from our promotions team tomorrow regarding those better internet plans. If you experience any other issues, please don't hesitate to call us back. Thank you for being an ABC customer, and have a wonderful day!

Customer: Thank you, you too. Bye!

Agent: Goodbye!
"""


async def test_get_rubric():
    """Test getting the scoring rubric."""
    print("\n" + "=" * 80)
    print("TEST 1: Get Scoring Rubric")
    print("=" * 80)

    rubric = get_scoring_rubric()
    print(f"\nRubric has {len(rubric['categories'])} categories")
    print(f"Total possible points: {rubric['total_possible_points']}")
    print("\nCategories:")
    for category_name, category_data in rubric["categories"].items():
        print(f"  - {category_name}: {category_data['description']}")
        print(f"    Criteria: {len(category_data['criteria'])}")


async def test_analyze_summary():
    """Test quick call summary (no full scoring)."""
    print("\n" + "=" * 80)
    print("TEST 2: Analyze Call Summary (Fast)")
    print("=" * 80)

    print("\nAnalyzing transcript...")
    result = await analyze_call_summary(SAMPLE_TRANSCRIPT)

    print(f"\nStatus: {result.get('status')}")

    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return

    summary = result.get("summary", {})
    print(f"\nBrief Summary:")
    print(f"  {summary.get('brief_summary', 'N/A')}")
    print(f"\nCustomer Issue:")
    print(f"  {summary.get('customer_issue', 'N/A')}")
    print(f"\nResolution:")
    print(f"  {summary.get('resolution_provided', 'N/A')}")
    print(f"\nSentiment: {summary.get('customer_sentiment', 'N/A')}")
    print(f"Category: {summary.get('call_category', 'N/A')}")


async def test_full_grading():
    """Test full call grading with quality scores."""
    print("\n" + "=" * 80)
    print("TEST 3: Full Call Grading")
    print("=" * 80)

    print("\nGrading transcript (this may take 30-60 seconds)...")
    result = await grade_call_transcript(
        transcript=SAMPLE_TRANSCRIPT,
        call_metadata={
            "customer_id": "CUST-12345",
            "agent_id": "AGT-SARAH",
            "call_category": "technical_support",
        },
    )

    print(f"\nStatus: {result.get('status')}")

    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return

    # Print overall results
    print(f"\n{'─' * 80}")
    print(f"OVERALL GRADE: {result.get('overall_grade', 'N/A')}")
    print(f"{'─' * 80}")

    if "quality_scores" in result:
        scores = result["quality_scores"]
        print(f"\nTotal Points: {scores.get('total_points')}/{scores.get('max_possible_points')}")
        print(f"Percentage: {scores.get('percentage_score', 0):.1f}%")

        print("\n✓ STRENGTHS:")
        for strength in scores.get("strengths", []):
            print(f"  • {strength}")

        print("\n△ AREAS FOR IMPROVEMENT:")
        for area in scores.get("areas_for_improvement", []):
            print(f"  • {area}")

        if scores.get("compliance_issues"):
            print("\n⚠ COMPLIANCE ISSUES:")
            for issue in scores["compliance_issues"]:
                print(f"  • {issue}")

        if scores.get("escalation_recommended"):
            print("\n🚩 ESCALATION RECOMMENDED")

        # Show sample category scores
        print("\n📊 SAMPLE CATEGORY SCORES:")
        categories = ["greeting", "communication", "resolution", "professionalism", "closing"]
        for category in categories:
            if category in scores:
                category_data = scores[category]
                print(f"\n{category.upper()}:")
                # Show first criterion as example
                for criterion_name, criterion_data in list(category_data.items())[
                    :1
                ]:  # Just first one
                    print(f"  {criterion_name}:")
                    print(f"    Score: {criterion_data['score']}/5 ({criterion_data['level']})")
                    print(f"    Evidence: {criterion_data['evidence'][:100]}...")

    print(f"\n{'─' * 80}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("MCP SERVER FUNCTIONALITY TEST")
    print("=" * 80)
    print("\nThis script tests the MCP server tools locally.")
    print("Make sure you have OPENAI_API_KEY set in your environment.\n")

    try:
        # Test 1: Get rubric (fast, no API calls)
        await test_get_rubric()

        # Test 2: Quick summary (faster, less expensive)
        await test_analyze_summary()

        # Test 3: Full grading (slower, more comprehensive)
        user_input = input("\n\nRun full grading test? (This uses OpenAI API) [y/N]: ")
        if user_input.lower() == "y":
            await test_full_grading()
        else:
            print("\nSkipping full grading test.")

        print("\n" + "=" * 80)
        print("✓ ALL TESTS COMPLETE")
        print("=" * 80)
        print("\nIf all tests passed, your MCP server is ready to use!")
        print("See docs/mcp_server.md for Claude Desktop setup instructions.\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
