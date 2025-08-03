from flask import Flask, request, jsonify, render_template
import openai
import os
from flask_cors import CORS

# Set your OpenAI key here or via environment variable
openai.api_key ="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"
print("Using OpenAI key:", openai.api_key)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

PRODUCTS = [
    {"name": "European Call/Put Option", "type": "Vanilla Option", "risk": "Low to Medium"},
    {"name": "American Call/Put Option", "type": "Vanilla Option", "risk": "Low to Medium"},
    {"name": "Barrier Option", "type": "Exotic Option: Up/Down, In/Out, auto-type", "risk": "Medium to High"},
    {"name": "Digital Option", "type": "Cash-or-nothing, Asset-or-nothing, Double Digital", "risk": "High"},
    {"name": "Asian Option", "type": "Arithmetic and Geometric, Monte Carlo supported", "risk": "Medium"},
    {"name": "Lookback Option", "type": "Fixed and Floating Strike", "risk": "Medium to High"},
    {"name": "One-Touch Option", "type": "Binary payoff with barrier monitoring", "risk": "High"},
    {"name": "Compound Option", "type": "Option on Option with nested pricing", "risk": "High"},
    {"name": "Chooser Option", "type": "Flexible call/put selection at preset dates", "risk": "Medium to High"},
    {"name": "Cliquet Option", "type": "Periodic resets, forward-start features", "risk": "Medium"},
    {"name": "Basket Option", "type": "Multi-asset with correlation structure", "risk": "Medium to High"},
    {"name": "Rainbow Option", "type": "Multi-asset, call on max/min and combos", "risk": "High"},
    {"name": "Variance Swap", "type": "Volatility-based derivative, fair strike calc", "risk": "High"},
    {"name": "Range Note", "type": "Barrier-monitored structured product with local vol trees", "risk": "Medium"}
]

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    print("Received:", user_input)

    product_list = "\n".join([f"- {p['name']}: {p['type']} (Risk: {p['risk']})" for p in PRODUCTS])

    prompt = f"""
You are a financial product recommendation assistant.
Use the following product list to answer questions and recommend products:
{product_list}

User: {user_input}
Assistant:
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful financial product recommendation assistant. Only suggest products from the list provided. Understand the user's goals, risk appetite, and preferences. Recommend one or more suitable financial instruments from the list and explain your reasoning in clear, professional language. Use plain English where possible. If the user asks for help or examples, explain the products using analogies or investor profiles. Your job is to help users pick the best product based on their goals (e.g., income, speculation, hedging), risk tolerance (low/medium/high), and market outlook. EXPLAIN PLAINLY AS IF THEY HAVE NO PRIOR FINANCE EXPERiENCE, RESPOND 3 SENTENCES MAX"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    reply = response.choices[0].message.content.strip()
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

