gdn_explanation_prompt = """

※ Model Overview:
GDN (Graph Detection Network) is a model that detects anomalies in multivariate time-series data by leveraging Graph Attention Networks. It analyzes the relationships between time-series features and assigns attention scores to neighbors. This allows a weighted sum of the features to be calculated, which is then passed through an activation function to generate the output.
For each metric, the model's predicted value is compared to the actual observed value from the system. The difference between these two values impacts the anomaly score, and the contribution of each metric is expressed as a percentage. The sum of all contributions across metrics equals 100, indicating the relative importance of each metric in the detected anomaly."""
