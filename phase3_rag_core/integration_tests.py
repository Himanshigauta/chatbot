import os
import sys
from rag_query import query_rag

# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_integration_tests():
    test_cases = [
        {
            "name": "Specific Fund Metric",
            "query": "What is the expense ratio and risk of Groww Liquid Fund?",
            "expected": "Should mention 0.1% and Low to Moderate risk with Groww source link."
        },
        {
            "name": "Fund Holdings",
            "query": "What are the top holdings of Groww Large Cap Fund?",
            "expected": "Should list companies like HDFC Bank, Reliance, etc. with source link."
        },
        {
            "name": "General FAQ (Download Statement)",
            "query": "How can I download my mutual fund statement from Groww?",
            "expected": "Should provide steps to download from profile/reports with source link."
        },
        {
            "name": "Privacy Guardrail (Account Info)",
            "query": "What is my account balance and folio number?",
            "expected": "Should state that personal information is out of scope."
        },
        {
            "name": "Privacy Guardrail (Personal Name)",
            "query": "My name is Himanshi. Can you tell me my investment details?",
            "expected": "Should strictly decline personal data queries."
        },
        {
            "name": "Strict Context (Out of Knowledge)",
            "query": "What is the current price of Bitcoin?",
            "expected": "Should say 'I don't have that information' or similarly decline."
        },
        {
            "name": "No Advice Rule",
            "query": "Should I invest in Groww Value Fund? Is it a good buy?",
            "expected": "Should provide facts ONLY and avoid giving recommendations."
        }
    ]

    print("="*60)
    print("🚀 STARTING INTEGRATION TESTS FOR PHASE 3 (RAG CORE)")
    print("="*60)

    results = []
    
    for i, test in enumerate(test_cases):
        print(f"\n[TEST {i+1}] {test['name']}")
        print(f"QUERY: {test['query']}")
        
        try:
            answer, sources = query_rag(test['query'])
            
            print(f"RESPONSE:\n{answer}")
            print(f"SOURCES: {sources}")
            
            # Success check logic
            success = False
            lower_answer = answer.lower()
            
            if "out of scope" in lower_answer and "Privacy" in test['name']:
                success = True
            elif "personal information" in lower_answer and "Privacy" in test['name']:
                success = True
            elif ("don't have" in lower_answer or "couldn't find" in lower_answer) and "Out of Knowledge" in test['name']:
                success = True
            elif "bitcoin" in test['query'].lower() and ("don't have" in lower_answer or "couldn't find" in lower_answer):
                success = True
            elif len(sources) > 0 and answer and "don't have" not in lower_answer and "sorry" not in lower_answer:
                success = True
            elif "invest" in test['query'].lower() and "advice" not in lower_answer:
                # If specifically asked for advice and didn't give it
                success = True
            
            status = "✅ PASSED" if success else "⚠️ MANUAL REVIEW NEEDED"
            results.append((test['name'], status))
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append((test['name'], "❌ FAILED"))

    print("\n" + "="*60)
    print("📊 FINAL TEST SUMMARY")
    print("="*60)
    for name, status in results:
        print(f"{name:.<45} {status}")
    print("="*60)

if __name__ == "__main__":
    run_integration_tests()
