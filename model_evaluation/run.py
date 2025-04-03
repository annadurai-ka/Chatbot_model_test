from utils import load_evaluation_dataset
from evaluate_retrieval import evaluate_retrieval
from evaluate_responses import evaluate_responses
from app import create_qa_chain
from app import create_retriever_from_df
from app import fetch_metadata
from app import fetch_reviews
asin = "B07LFV749P"
dataset = load_evaluation_dataset("evaluation_framework/evaluation_dataset.json")
review_df = fetch_reviews(asin)
meta_df = fetch_metadata(asin)
retriever = create_retriever_from_df(review_df)
qa_chain = create_qa_chain(retriever)
retriever_results = evaluate_retrieval(dataset, retriever)
print("Retrieval Performance:", retriever_results)

response_results = evaluate_responses(dataset, qa_chain)
print("Response Quality:", response_results)
