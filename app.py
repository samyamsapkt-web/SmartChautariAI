from flask import Flask, render_template, request, jsonify
import json
import os
from groq import Groq

app = Flask(__name__)

# Load menu once at startup
with open("menu.json", "r", encoding="utf-8") as f:
    menu_data = json.load(f)["menu"]

# Build a compact menu string to inject into every prompt
def build_menu_context():
    lines = []
    current_cat = None
    for item in menu_data:
        cat = item["category"].title()
        if cat != current_cat:
            lines.append(f"\n[{cat}]")
            current_cat = cat
        halal = " (Halal)" if item.get("halal") else ""
        ingredients = ", ".join(item.get("ingredients", []))
        lines.append(
            f"  - {item['name']} | ${item['price']:.2f}{halal} | "
            f"{item['description']} | Ingredients: {ingredients}"
        )
    return "\n".join(lines)

MENU_CONTEXT = build_menu_context()

SYSTEM_PROMPT = f"""You are a friendly and knowledgeable menu assistant for a restaurant.
Your job is to help customers find menu items, answer questions about ingredients, dietary options, prices, and make recommendations.

Here is the full menu you must reference — do not invent items that aren't listed here:

{MENU_CONTEXT}

Guidelines:
- Answer naturally and conversationally, like a helpful restaurant staff member.
- If a customer asks about a specific item, give its name, price, description, and ingredients.
- If an item comes in multiple sizes, list all sizes and their prices.
- If a customer asks what's halal, vegetarian, vegan, or spicy, filter and list appropriately.
- If asked for the full menu, list everything grouped by category.
- If you don't recognise something as a menu item, politely say it's not on the menu and suggest alternatives.
- Keep responses concise. Don't pad with unnecessary filler.
- Do not make up prices, items, or ingredients.
- Use ✅ to mark Halal items when listing multiple items."""

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Please ask about a menu item."})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": question}
            ]
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = "Sorry, I'm having trouble right now. Please try again in a moment."
        print(f"Groq API error: {e}")

    return jsonify({"answer": answer})

# =========================
# RUN
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
