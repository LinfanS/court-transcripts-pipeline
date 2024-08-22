"""Python script to calculate the total cost of using the GPT-4o-mini model on the batch pipeline"""

from ast import literal_eval

# pricing info available at https://openai.com/api/pricing/
INPUT_COST_PER_MILLION_TOKENS = 0.15
OUTPUT_COST_PER_MILLION_TOKENS = 0.60


def calculate_cost(file_name):
    """Calculate the total cost of using the GPT-4o-mini model"""
    output_tokens, input_tokens = 0, 0

    with open(file_name, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if "GPT-4o-mini usage cost:" in line:
            cost_string = line.split(": ")[1]
            cost_list = literal_eval(cost_string)
            output_tokens += cost_list[0]
            input_tokens += cost_list[1]

    output_cost = (output_tokens / 1000000) * OUTPUT_COST_PER_MILLION_TOKENS
    input_cost = (input_tokens / 1000000) * INPUT_COST_PER_MILLION_TOKENS
    print(f"Output cost: ${output_cost:.2f}")
    print(f"Input cost: ${input_cost:.2f}")
    total_cost = output_cost + input_cost
    total_cost_usd = f"${total_cost:.2f}"
    return total_cost_usd


if __name__ == "__main__":
    print(calculate_cost("batch_pipeline.log"))  # $15.71
