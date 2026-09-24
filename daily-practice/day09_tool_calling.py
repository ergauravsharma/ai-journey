import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


# --- Step 1: The real function the model will call ---
def calculate(expression: str) -> float:
    """Evaluate a basic math expression like '15 * 23' or '(120 - 45) / 3'."""
    print(f"[calculate() was called with: {expression}]")
    return eval(expression)  # safe here since it's our own controlled demo


# --- Step 2: Describe the tool to the model ---
calculate_tool = types.FunctionDeclaration(
    name="calculate",
    description="Evaluate a mathematical expression and return the numeric result.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "expression": types.Schema(
                type=types.Type.STRING,
                description="A math expression to evaluate, e.g. '15 * 23'",
            ),
        },
        required=["expression"],
    ),
)

tools = types.Tool(function_declarations=[calculate_tool])


def ask_with_tool(question: str) -> str:
    # --- Step 3: Send the question + tool definition to the model ---
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=question,
        config=types.GenerateContentConfig(tools=[tools]),
    )

    part = response.candidates[0].content.parts[0]

    # --- Step 4: Check if the model wants to call our function ---
    if part.function_call:
        function_call = part.function_call
        print(f"[Model decided to call: {function_call.name}({dict(function_call.args)})]")

        # --- Step 5: Actually run the real function ---
        result = calculate(function_call.args["expression"])

        # --- Step 6: Send the result back so the model can give a final answer ---
        follow_up = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=question)]),
                types.Content(role="model", parts=[part]),
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name="calculate",
                            response={"result": result},
                        )
                    ],
                ),
            ],
            config=types.GenerateContentConfig(tools=[tools]),
        )
        return follow_up.text

    # If no tool call was needed, just return the direct answer
    return response.text


if __name__ == "__main__":
    question = "What is 347 multiplied by 892, minus 1500?"
    print(f"Question: {question}\n")
    answer = ask_with_tool(question)
    print(f"\nFinal Answer: {answer}")