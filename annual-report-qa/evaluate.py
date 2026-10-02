"""
Evaluation Script for Annual Report Q&A Assistant.
Evaluates 10 financial test questions against the indexed report,
validating retrieval accuracy, page citations, and hallucination suppression.
Outputs a clean Markdown evaluation table.
"""

import sys
import time
from typing import List, Dict, Any

import config
from rag_chain import FinancialRAGChain

TEST_SUITE = [
    {
        "id": 1,
        "question": "What was the total revenue in FY2024?",
        "expected_answer": "₹240,893 crore ($29.1 billion), representing a growth of 6.8% YoY.",
        "expected_pages": [1],
        "category": "Key Financials",
    },
    {
        "id": 2,
        "question": "What are the main risks mentioned by management?",
        "expected_answer": "Macroeconomic uncertainty, GenAI disruption, cybersecurity, geopolitical conflicts, forex volatility, talent retention.",
        "expected_pages": [3],
        "category": "Risk Management",
    },
    {
        "id": 3,
        "question": "How many employees does the company have?",
        "expected_answer": "601,546 employees as of March 31, 2024.",
        "expected_pages": [4],
        "category": "Human Capital",
    },
    {
        "id": 4,
        "question": "What is the dividend per share?",
        "expected_answer": "Total dividend of ₹73.00 per share (interim ₹27 + special ₹18 + final ₹28).",
        "expected_pages": [5],
        "category": "Shareholder Returns",
    },
    {
        "id": 5,
        "question": "What was the operating profit (EBIT) and operating margin in FY2024?",
        "expected_answer": "Operating profit was ₹59,314 crore and operating margin was 24.6%.",
        "expected_pages": [1],
        "category": "Key Financials",
    },
    {
        "id": 6,
        "question": "What was the net profit (profit after tax) for FY2024?",
        "expected_answer": "Net profit (PAT) was ₹46,099 crore (up 9.0% YoY).",
        "expected_pages": [1],
        "category": "Key Financials",
    },
    {
        "id": 7,
        "question": "What percentage of the workforce are women professionals?",
        "expected_answer": "35.6% of the workforce are women professionals (over 214,000 women).",
        "expected_pages": [4],
        "category": "Human Capital",
    },
    {
        "id": 8,
        "question": "What was the total value of the share buyback in FY2024?",
        "expected_answer": "₹17,000 crore completed in December 2023 at ₹4,150 per share.",
        "expected_pages": [5],
        "category": "Shareholder Returns",
    },
    {
        "id": 9,
        "question": "What was the company's long-term debt as of March 31, 2024?",
        "expected_answer": "Zero long-term debt (₹0) / unencumbered balance sheet.",
        "expected_pages": [6],
        "category": "Balance Sheet",
    },
    {
        "id": 10,
        "question": "What was the company's exact revenue from automotive sales in Germany?",
        "expected_answer": 'I could not find this in the report. (Tests hallucination suppression)',
        "expected_pages": [],
        "category": "Negative Test (Anti-Hallucination)",
    },
]


def run_evaluation(model_name: str = None) -> List[Dict[str, Any]]:
    rag = FinancialRAGChain(model_name=model_name)
    results = []

    print("\n" + "=" * 80)
    print("STARTING ANNUAL REPORT Q&A ASSISTANT EVALUATION (10 TEST CASES)")
    print(f"Model: {rag.primary_model_name} (with fallback resilience)")
    print("=" * 80 + "\n")

    for test in TEST_SUITE:
        qid = test["id"]
        q = test["question"]
        print(f"[{qid}/10] Testing: {q}")
        t0 = time.time()
        res = rag.query(q)
        duration = round(time.time() - t0, 2)

        ans = res["answer"].strip()
        sources = res["sources"]
        model_used = res["model_used"]

        # Check citation accuracy
        expected_p = test["expected_pages"]
        if expected_p:
            citation_match = any(p in sources for p in expected_p)
        else:
            # For negative test, should state not found
            citation_match = "not find" in ans.lower() or "not in the report" in ans.lower()

        # Grade result
        if qid == 10:
            is_correct = "could not find" in ans.lower() or "not found" in ans.lower() or "not mentioned" in ans.lower()
        else:
            is_correct = citation_match and len(ans) > 10

        status_badge = "✅ PASS" if is_correct else "⚠️ REVIEW"

        result_row = {
            "id": qid,
            "category": test["category"],
            "question": q,
            "expected_pages": expected_p,
            "retrieved_pages": sources,
            "expected_answer": test["expected_answer"],
            "generated_answer": ans,
            "status": status_badge,
            "duration": f"{duration}s",
            "model_used": model_used,
        }
        results.append(result_row)
        print(f"       -> Status: {status_badge} | Retrieved Pages: {sources} | Time: {duration}s\n")

    return results


def print_markdown_table(results: List[Dict[str, Any]]):
    print("\n" + "#" * 80)
    print("### Evaluation Results Table (Markdown for README)")
    print("#" * 80 + "\n")

    md = "| # | Category | Question | Expected Page | Retrieved Pages | Evaluation Result | Status |\n"
    md += "|---|---|---|---|---|---|---|\n"

    for r in results:
        exp_p = ", ".join(map(str, r["expected_pages"])) if r["expected_pages"] else "None (Negative Test)"
        ret_p = ", ".join(map(str, r["retrieved_pages"])) if r["retrieved_pages"] else "None"
        # truncate answer for table readability
        short_ans = r["generated_answer"].replace("\n", " ")[:90] + ("..." if len(r["generated_answer"]) > 90 else "")
        short_ans = short_ans.replace("|", "/")
        md += f"| {r['id']} | {r['category']} | {r['question']} | {exp_p} | {ret_p} | {short_ans} | {r['status']} |\n"

    print(md)
    return md


if __name__ == "__main__":
    results = run_evaluation()
    print_markdown_table(results)
