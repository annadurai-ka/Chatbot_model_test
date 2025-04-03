from typing import List, Dict

def evaluate_retrieval(test_queries: List[Dict], retriever, k: int = 5):
    """
    Evaluate retrieval performance using Precision@k and Recall@k.
    
    Args:
        test_queries (List[Dict]): List of test queries with relevant documents.
        retriever: The FAISS retriever object.
        k (int): Number of top-k documents to evaluate.
        
    Returns:
        Dict: Average Precision@k and Recall@k across all queries.
    """
    precision_scores = []
    recall_scores = []

    for test_query in test_queries:
        query = test_query["query"]
        relevant_docs = test_query["retrieved_docs"]

        # Retrieve top-k documents
        retrieved_docs = retriever.invoke(query)[:k]
        retrieved_texts = [doc.page_content for doc in retrieved_docs]
        print(f"Query: {query}")
        print(f"Relevant Docs: {relevant_docs}")
        print(f"Retrieved Docs: {retrieved_texts}")

        # Calculate Precision@k
        precision_at_k = len(set(relevant_docs) & set(retrieved_texts)) / len(retrieved_texts)
        precision_scores.append(precision_at_k)

        # Calculate Recall@k
        recall_at_k = len(set(relevant_docs) & set(retrieved_texts)) / len(relevant_docs)
        recall_scores.append(recall_at_k)

    avg_precision = sum(precision_scores) / len(precision_scores)
    avg_recall = sum(recall_scores) / len(recall_scores)

    return {
        "Precision@k": avg_precision,
        "Recall@k": avg_recall,
    }
