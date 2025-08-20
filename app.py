from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os, re
from difflib import SequenceMatcher

# --- API key ---
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not set in environment variables.")
client = OpenAI()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

PRODUCTS = [
    {"name": "European Option", "complexity": "Low – closed-form pricing (Black–Scholes), standard contracts",
     "suitability": "Beginner to Intermediate investors comfortable with basic risk",
     "functionality": "Provides leveraged exposure to directional bets with limited downside. Standardized, liquid, and widely used for hedging or speculation."},
    {"name": "American Option", "complexity": "Low to Medium – early exercise adds valuation complexity",
     "suitability": "Beginner to Intermediate investors with moderate trading experience",
     "functionality": "Offers the flexibility to exercise before expiry, useful for dividend capture or dynamic hedging."},
    {"name": "Barrier Option", "complexity": "Medium to High – path dependency and barrier monitoring required",
     "suitability": "Intermediate to Advanced investors willing to take higher event risk",
     "functionality": "Enables cheaper hedges or speculative structures by activating or nullifying the option at certain price levels. Attractive for risk-managed directional bets."},
    {"name": "Digital Option", "complexity": "High – discontinuous payoff, sensitive to volatility assumptions",
     "suitability": "Advanced, risk-tolerant investors/speculators",
     "functionality": "Delivers a fixed payoff if the underlying meets conditions. Used for high-convexity bets, binary event risk, or precise payoff shaping."},
    {"name": "Asian Option", "complexity": "Medium – averaging reduces volatility, often priced with simulation",
     "suitability": "Intermediate investors seeking smoother exposure and less path risk",
     "functionality": "Payoff depends on average price over time, reducing manipulation risk and volatility exposure. Useful for commodities, currencies, or smoothing returns."},
    {"name": "Lookback Option", "complexity": "Medium to High – payoff depends on extrema, requires advanced models",
     "suitability": "Advanced investors comfortable with complex risk/reward profiles",
     "functionality": "Allows the holder to 'look back' and use the optimal price over the life of the option. Used for capturing best execution and reducing regret risk."},
    {"name": "One-Touch Option", "complexity": "High – binary barrier product, highly sensitive to vol and barrier proximity",
     "suitability": "Advanced investors/speculators willing to take large tail risks",
     "functionality": "Pays a fixed amount if the barrier is touched. Common for hedging credit/currency risks or leveraged bets on sharp price moves."},
    {"name": "Compound Option", "complexity": "High – option on option, nested pricing adds strong convexity effects",
     "suitability": "Advanced investors with derivatives expertise",
     "functionality": "Option on another option, enabling staged exposure or leverage on volatility itself. Useful in corporate finance, structured deals, or vol trading."},
    {"name": "Range Note", "complexity": "Medium – structured payoff with barrier monitoring, local vol trees",
     "suitability": "Intermediate investors seeking yield enhancement with event risk",
     "functionality": "Pays enhanced coupons if the underlying stays within a price range. Used for yield generation in sideways markets."},
    {"name": "Normal Token Swap", "complexity": "Low – basic AMM or orderbook swap",
     "suitability": "All levels; suitable for any user needing simple asset exchange",
     "functionality": "Swaps one token for another via liquidity pools or orderbooks. Core building block of DeFi for portfolio rebalancing, hedging, or accessing new assets."},
    {"name": "Bridging", "complexity": "Operational – cross-chain communication and smart contract risk",
     "suitability": "All levels, but medium risk tolerance required for smart contract and liquidity risks",
     "functionality": "Moves assets across blockchains, enabling access to liquidity, yield, or applications on other chains. Critical for multi-chain strategies."},
    {"name": "Porting", "complexity": "Operational – position or exposure transfer across systems",
     "suitability": "All levels; especially useful for professionals managing cross-platform portfolios",
     "functionality": "Transfers open positions, exposures, or assets between environments (e.g., CEX to DeFi). Reduces friction, improves capital efficiency, and supports continuity of strategies."}
]
PRODUCT_NAMES = [p["name"] for p in PRODUCTS]

def _first_sentence(text: str) -> str:
    """Collapse whitespace and return exactly the first sentence."""
    txt = " ".join((text or "").split())
    # Split at first terminator; treat ; – — as terminators too
    m = re.search(r'[.!?]|[;–—]', txt)
    return (txt[:m.start()+1] if m else txt).strip()

def _best_name_from_text_or_user(reply: str, user_input: str) -> str:
    """Pick a product name by (1) direct mention in reply, else (2) fuzzy match vs reply/user_input."""
    rl = (reply or "").lower()
    for name in PRODUCT_NAMES:
        if name.lower() in rl:
            return name
    # Fuzzy vs reply & user input
    corpus = [reply or "", user_input or ""]
    scores = []
    for name in PRODUCT_NAMES:
        score = max(SequenceMatcher(None, name.lower(), c.lower()).ratio() for c in corpus)
        scores.append((score, name))
    scores.sort(reverse=True)
    return scores[0][1]  # best

def enforce_single_sentence_and_prefix(reply: str, user_input: str) -> str:
    """Ensure output is 'ExactProductName: <one-sentence blurb>'."""
    sent = _first_sentence(reply)

    # If already in the correct "Name: ..." shape (case-insensitive), normalize the name’s casing.
    for name in PRODUCT_NAMES:
        prefix = f"{name}:"
        if sent.lower().startswith(prefix.lower()):
            rest = sent[len(prefix):].strip()
            rest = _first_sentence(rest)
            rest = re.sub(r'^[,:;.\-\s]+', '', rest)  # strip stray punctuation
            return f"{name}: {rest}"

    # Otherwise, select a product name and rebuild
    chosen = _best_name_from_text_or_user(sent, user_input)

    # Remove the chosen name if it appears later to avoid duplication
    rest = re.sub(re.escape(chosen), "", sent, count=1, flags=re.IGNORECASE).lstrip(": -–—").strip()
    rest = _first_sentence(rest)
    rest = re.sub(r'^[,:;.\-\s]+', '', rest)
    if not rest:
        rest = "Good fit for your request."
    return f"{chosen}: {rest}"

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = (request.json.get("message") or "").strip()

    product_list = "\n".join([
        f"- {p['name']}: {p['complexity']} | Suitability: {p['suitability']} | Functionality: {p['functionality']}"
        for p in PRODUCTS
    ])

    system_instr = (
        "Only suggest products from the provided list. "
        "Reply with exactly ONE sentence. "
        "Start with the EXACT product name from the list, then a colon and a concise rationale tailored to the user's request. "
        "Do not offer multiple products, and do not copy phrases verbatim from the list."
    )

    prompt = f"""Here is the available product knowledge base:
{product_list}

User: {user_input}
Assistant:"""

    try:
        resp = client.responses.create(
            model="gpt-5",
            input=[
                {"role": "system", "content": system_instr},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_output_tokens=120,
            store=False,
        )

        raw = (resp.output_text or "").strip()
        reply = enforce_single_sentence_and_prefix(raw, user_input)
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
