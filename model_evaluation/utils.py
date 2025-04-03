import json

def load_evaluation_dataset(file_path):
    """
    Load the evaluation dataset from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file containing the dataset.
        
    Returns:
        List[Dict]: List of evaluation queries and expected results.
    """
    with open(file_path, "r") as f:
        return json.load(f)
