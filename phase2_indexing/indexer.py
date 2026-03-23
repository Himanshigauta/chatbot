import json
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Configuration
DATA_FILES = ["../phase1_data_acquisition/mutual_fund_data_full.json"]
CHROMA_PATH = "chroma_db_full"

def format_fund_document(fund):
    """Transform fund JSON into a descriptive text string for indexing."""
    name = fund.get('scheme_name', 'N/A')
    amc = fund.get('amc_info', {}).get('name', 'N/A')
    category = f"{fund.get('category', 'N/A')} - {fund.get('sub_category', 'N/A')}"
    expense = fund.get('expense_ratio', 'N/A')
    exit_load = fund.get('exit_load', 'N/A')
    
    # Risk Extraction
    risk = fund.get('risk', 'N/A')
    if not risk or risk == 'N/A':
        risk = fund.get('nfo_risk', 'N/A')
    
    benchmark = fund.get('benchmark_name', 'N/A')
    min_sip = fund.get('min_sip_investment', 'N/A')
    lock_in = fund.get('lock_in', {}).get('years', 'None')
    
    # Returns
    returns = fund.get('return_stats', [{}])[0]
    ret_3y = returns.get('return3y', 'N/A')
    ret_5y = returns.get('return5y', 'N/A')
    
    # Analysis (Pros & Cons)
    analysis_text = ""
    analysis = fund.get('analysis', [])
    if analysis:
        pros = [a.get('text') for a in analysis if a.get('is_positive') and a.get('text')]
        cons = [a.get('text') for a in analysis if not a.get('is_positive') and a.get('text')]
        analysis_text = f"\nPros:\n- " + "\n- ".join(pros) + f"\nCons:\n- " + "\n- ".join(cons) if (pros or cons) else ""
    
    # AMC Extra Info
    amc_extra = fund.get('amc_extra', {})
    key_info = amc_extra.get('key_info', '')
    closer_look = amc_extra.get('closer_look', '')

    # Holdings
    holdings_text = ""
    holdings = fund.get('holdings', [])
    if holdings:
        top_holdings = [f"{h.get('company_name')} ({h.get('corpus_per', 0):.2f}%)" for h in holdings[:10]]
        holdings_text = "\nTop Holdings:\n- " + "\n- ".join(top_holdings)

    # Trim description to save tokens
    desc = fund.get('description', 'N/A')
    if len(desc) > 300: desc = desc[:300] + "..."

    # BOOST: Prepend the fund name multiple times to increase its vector weight for search
    boosted_name = (name + " ") * 3

    doc_text = f"""
{boosted_name}
Mutual Fund Name: {name}
AMC: {amc}
Category: {category}
Expense Ratio: {expense}%
Exit Load: {exit_load}
Risk Profile: {risk}
Benchmark: {benchmark}
Minimum SIP: \u20b9{min_sip}
Lock-in Period: {lock_in} years
Returns (3Y): {ret_3y}%
Returns (5Y): {ret_5y}%
About: {desc}
{analysis_text}
{holdings_text}
Source URL: {fund.get('source_url')}
    """.strip()
    
    return doc_text

def index_data():
    files = DATA_FILES
    documents = []

    for data_file in files:
        if not os.path.exists(data_file):
            print(f"Warning: {data_file} not found. Skipping.")
            continue

        with open(data_file, 'r') as f:
            data = json.load(f)

        print(f"Processing {len(data)} items from {data_file}...")
        
        for item in data:
            # 1. Main Fund Document
            content = format_fund_document(item)
            metadata = {
                "source": item.get('source_url'),
                "fund_name": item.get('scheme_name'),
                "amc": item.get('amc_info', {}).get('name', 'N/A')
            }
            documents.append(Document(page_content=content, metadata=metadata))
            
            # 2. Add individual FAQs as separate search hits
            faqs = item.get('faqs', [])
            for faq in faqs:
                q = faq.get('question')
                a = faq.get('answer')
                faq_content = f"Question: {q}\nAnswer: {a}\nContext: This FAQ is for {item.get('scheme_name')}.\nSource URL: {item.get('source_url')}"
                faq_metadata = {
                    "source": item.get('source_url'),
                    "fund_name": item.get('scheme_name'),
                    "type": "faq"
                }
                documents.append(Document(page_content=faq_content, metadata=faq_metadata))

    print("Initializing Embeddings (HuggingFace)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print(f"Creating Vector Store at {CHROMA_PATH} (Resetting)...")
    import shutil
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print("Indexing complete!")

if __name__ == "__main__":
    index_data()
