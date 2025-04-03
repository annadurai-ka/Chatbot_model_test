from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge

def evaluate_responses(test_queries, qa_chain):
    """
    Evaluate response quality using BLEU and ROUGE metrics.
    
    Args:
        test_queries (List[Dict]): List of test queries with expected responses.
        qa_chain: The QA chain object used to generate responses.
    
    Returns:
        Dict: Average BLEU and ROUGE-L scores across all queries.
    """
    bleu_scores = []
    rouge = Rouge()
    rouge_scores = []

    for test_query in test_queries:
        query = test_query["query"]
        expected_response = test_query["expected_response"]

        # Generate response using QA chain
        response = qa_chain.invoke({"question": query})  # Pass "question" as the input key
        generated_response = response["answer"]  # Extract only the answer

        # Debugging output (optional)
        print(f"Query: {query}")
        print(f"Expected Response: {expected_response}")
        print(f"Generated Response: {generated_response}")

        # Calculate BLEU score
        bleu_score = sentence_bleu([expected_response.split()], generated_response.split())
        bleu_scores.append(bleu_score)

        # Calculate ROUGE scores
        rouge_score = rouge.get_scores(generated_response, expected_response)
        rouge_scores.append(rouge_score[0]["rouge-l"]["f"])

    avg_bleu = sum(bleu_scores) / len(bleu_scores)
    avg_rouge_l = sum(rouge_scores) / len(rouge_scores)

    return {
        "BLEU Score": avg_bleu,
        "ROUGE-L Score": avg_rouge_l,
    }
