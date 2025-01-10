import ell
ell.init(store="./logdir")  # Enable versioning and storage

# 1. Define an LMP:
@ell.simple(model="gpt-4o", max_tokens=10)
def classify_sentiment(text: str):
    """You are a sentiment classifier. Return 'positive' or 'negative'."""
    return f"Classify sentiment: {text}"

# 2. A small dataset:
dataset = [
    {"input": {"text": "I love this product!"}, "expected_output": "positive"},
    {"input": {"text": "This is terrible."}, "expected_output": "negative"}
]

# 3. A metric function that checks correctness:
def accuracy_metric(datapoint, output):
    return float(datapoint["expected_output"].lower() in output.lower())

# 4. Constructing the eval:
eval = ell.evaluation.Evaluation(
    name="sentiment_eval",
    dataset=dataset,
    metrics={"accuracy": accuracy_metric}
)

# Run the eval:
result = eval.run(classify_sentiment)
print("Average accuracy:", result.results.metrics["accuracy"].mean())