from flask import Flask, request, jsonify, render_template
import openai
import os
from flask_cors import CORS

# Set your OpenAI key here or via environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY not set in environment variables.")


app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

PRODUCTS = [
    {
        "name": "European Option",
        "complexity": "Low – closed-form pricing (Black–Scholes), standard contracts",
        "suitability": "Beginner to Intermediate investors comfortable with basic risk",
        "functionality": "Provides leveraged exposure to directional bets with limited downside. Standardized, liquid, and widely used for hedging or speculation."
    },
    {
        "name": "American Option",
        "complexity": "Low to Medium – early exercise adds valuation complexity",
        "suitability": "Beginner to Intermediate investors with moderate trading experience",
        "functionality": "Offers the flexibility to exercise before expiry, useful for dividend capture or dynamic hedging."
    },
    {
        "name": "Barrier Option",
        "complexity": "Medium to High – path dependency and barrier monitoring required",
        "suitability": "Intermediate to Advanced investors willing to take higher event risk",
        "functionality": "Enables cheaper hedges or speculative structures by activating or nullifying the option at certain price levels. Attractive for risk-managed directional bets."
    },
    {
        "name": "Digital Option",
        "complexity": "High – discontinuous payoff, sensitive to volatility assumptions",
        "suitability": "Advanced, risk-tolerant investors/speculators",
        "functionality": "Delivers a fixed payoff if the underlying meets conditions. Used for high-convexity bets, binary event risk, or precise payoff shaping."
    },
    {
        "name": "Asian Option",
        "complexity": "Medium – averaging reduces volatility, often priced with simulation",
        "suitability": "Intermediate investors seeking smoother exposure and less path risk",
        "functionality": "Payoff depends on average price over time, reducing manipulation risk and volatility exposure. Useful for commodities, currencies, or smoothing returns."
    },
    {
        "name": "Lookback Option",
        "complexity": "Medium to High – payoff depends on extrema, requires advanced models",
        "suitability": "Advanced investors comfortable with complex risk/reward profiles",
        "functionality": "Allows the holder to 'look back' and use the optimal price over the life of the option. Used for capturing best execution and reducing regret risk."
    },
    {
        "name": "One-Touch Option",
        "complexity": "High – binary barrier product, highly sensitive to vol and barrier proximity",
        "suitability": "Advanced investors/speculators willing to take large tail risks",
        "functionality": "Pays a fixed amount if the barrier is touched. Common for hedging credit/currency risks or leveraged bets on sharp price moves."
    },
    {
        "name": "Compound Option",
        "complexity": "High – option on option, nested pricing adds strong convexity effects",
        "suitability": "Advanced investors with derivatives expertise",
        "functionality": "Option on another option, enabling staged exposure or leverage on volatility itself. Useful in corporate finance, structured deals, or vol trading."
    },
    {
        "name": "Range Note",
        "complexity": "Medium – structured payoff with barrier monitoring, local vol trees",
        "suitability": "Intermediate investors seeking yield enhancement with event risk",
        "functionality": "Pays enhanced coupons if the underlying stays within a price range. Used for yield generation in sideways markets."
    },
    {
        "name": "Normal Token Swap",
        "complexity": "Low – basic AMM or orderbook swap",
        "suitability": "All levels; suitable for any user needing simple asset exchange",
        "functionality": "Swaps one token for another via liquidity pools or orderbooks. Core building block of DeFi for portfolio rebalancing, hedging, or accessing new assets."
    },
    {
        "name": "Bridging",
        "complexity": "Operational – cross-chain communication and smart contract risk",
        "suitability": "All levels, but medium risk tolerance required for smart contract and liquidity risks",
        "functionality": "Moves assets across blockchains, enabling access to liquidity, yield, or applications on other chains. Critical for multi-chain strategies."
    },
    {
        "name": "Porting",
        "complexity": "Operational – position or exposure transfer across systems",
        "suitability": "All levels; especially useful for professionals managing cross-platform portfolios",
        "functionality": "Transfers open positions, exposures, or assets between environments (e.g., CEX to DeFi). Reduces friction, improves capital efficiency, and supports continuity of strategies."
    }
]

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    product_list = "\n".join([
    f"- {p['name']}: {p['complexity']} | Suitability: {p['suitability']} | Functionality: {p['functionality']}"
    for p in PRODUCTS
    ])

    prompt = f"""
    Here is the available product knowledge base:
    {product_list}
    
    User: {user_input}
    Assistant:
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Only suggest products from the list provided, respond 1 sentences max. Make sure to name the product first when responding as the front end will look for the name so it needs to be exact. then give a breif discription/resopnd to the users promt. Also you need to be very concise. Dont offer mulitple products. Be right to the point, dont run on about anything. Please do not copy paste from the instruction but use your own words."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )

    reply = response.choices[0].message.content.strip()
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

