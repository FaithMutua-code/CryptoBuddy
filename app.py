from flask import Flask, render_template, request, jsonify
import datetime

app = Flask(__name__)

# Predefined cryptocurrency database
crypto_db = {
    "Bitcoin": {
        "price_trend": "rising",
        "market_cap": "high",
        "energy_use": "high",
        "sustainability_score": 3
    },
    "Ethereum": {
        "price_trend": "stable",
        "market_cap": "high",
        "energy_use": "medium",
        "sustainability_score": 6
    },
    "Cardano": {
        "price_trend": "rising",
        "market_cap": "medium",
        "energy_use": "low",
        "sustainability_score": 8
    },
    "Solana": {
        "price_trend": "rising",
        "market_cap": "medium",
        "energy_use": "low",
        "sustainability_score": 7
    },
    "Polkadot": {
        "price_trend": "stable",
        "market_cap": "medium",
        "energy_use": "low",
        "sustainability_score": 9
    }
}

def analyze_profitability():
    """Find the most profitable cryptocurrencies"""
    profitable_coins = []
    for coin, data in crypto_db.items():
        if data["price_trend"] == "rising" and data["market_cap"] in ["high", "medium"]:
            profitable_coins.append((coin, data))
    
    if profitable_coins:
        profitable_coins.sort(key=lambda x: (1 if x[1]["market_cap"] == "high" else 0, x[1]["sustainability_score"]), reverse=True)
        return profitable_coins[0]
    return None

def analyze_sustainability():
    """Find the most sustainable cryptocurrencies"""
    sustainable_coins = []
    for coin, data in crypto_db.items():
        if data["energy_use"] == "low" and data["sustainability_score"] >= 7:
            sustainable_coins.append((coin, data))
    
    if sustainable_coins:
        sustainable_coins.sort(key=lambda x: x[1]["sustainability_score"], reverse=True)
        return sustainable_coins[0]
    return None

def get_balanced_recommendation():
    """Find a balance between profitability and sustainability"""
    balanced_coins = []
    for coin, data in crypto_db.items():
        if data["price_trend"] in ["rising", "stable"] and data["sustainability_score"] >= 5:
            profit_score = 3 if data["price_trend"] == "rising" else 1
            market_score = 3 if data["market_cap"] == "high" else 2 if data["market_cap"] == "medium" else 1
            sustainability_score = data["sustainability_score"]
            combined_score = profit_score + market_score + sustainability_score
            balanced_coins.append((coin, data, combined_score))
    
    if balanced_coins:
        balanced_coins.sort(key=lambda x: x[2], reverse=True)
        return balanced_coins[0]
    return None

def get_coin_info(coin_name):
    """Get information about a specific coin"""
    return crypto_db.get(coin_name)

def process_message(user_input):
    """Process user input and return bot response"""
    user_input = user_input.lower().strip()
    
    if any(word in user_input for word in ['profit', 'make money', 'trending', 'rising']):
        coin_data = analyze_profitability()
        if coin_data:
            coin, data = coin_data
            return {
                "response": f"📈 For maximum profitability, consider **{coin}**!",
                "details": f"""
                **Why {coin}:**
                • Price trend: {data['price_trend'].upper()}
                • Market cap: {data['market_cap'].upper()} (good stability)
                • Sustainability score: {data['sustainability_score']}/10
                
                💡 *Remember: High profit potential often comes with higher risk!*
                """
            }
        else:
            return {
                "response": "No highly profitable coins found in current market conditions. Consider balanced options instead."
            }
    
    elif any(word in user_input for word in ['sustainable', 'eco', 'green', 'environment']):
        coin_data = analyze_sustainability()
        if coin_data:
            coin, data = coin_data
            return {
                "response": f"🌱 For sustainability, I recommend **{coin}**!",
                "details": f"""
                **Why {coin}:**
                • Energy use: {data['energy_use'].upper()}
                • Sustainability score: {data['sustainability_score']}/10 ⭐
                • Price trend: {data['price_trend'].upper()}
                • Market cap: {data['market_cap'].upper()}
                
                🌍 *Great choice for environmentally conscious investing!*
                """
            }
        else:
            return {
                "response": "No highly sustainable coins found in the database."
            }
    
    elif any(word in user_input for word in ['balanced', 'best', 'recommend', 'advice']):
        coin_data = get_balanced_recommendation()
        if coin_data:
            coin, data, score = coin_data
            return {
                "response": f"⚖️ For a balanced approach, I suggest **{coin}**!",
                "details": f"""
                **Why {coin}:**
                • Good balance of profit and sustainability
                • Price trend: {data['price_trend'].upper()}
                • Market cap: {data['market_cap'].upper()}
                • Sustainability: {data['sustainability_score']}/10
                • Energy use: {data['energy_use'].upper()}
                
                🎯 *This coin offers a great risk-reward-sustainability balance!*
                """
            }
        else:
            return {
                "response": "Couldn't find a balanced recommendation at this time."
            }
    
    elif any(word in user_input for word in ['bitcoin', 'ethereum', 'cardano', 'solana', 'polkadot']):
        for coin in crypto_db:
            if coin.lower() in user_input:
                data = crypto_db[coin]
                sustainability_note = "🌟 Highly sustainable!" if data['sustainability_score'] >= 7 else "⚠️ Has sustainability concerns." if data['sustainability_score'] <= 4 else ""
                return {
                    "response": f"💰 Information about **{coin}**:",
                    "details": f"""
                    **{coin} Details:**
                    • Price Trend: {data['price_trend'].upper()}
                    • Market Cap: {data['market_cap'].upper()}
                    • Energy Use: {data['energy_use'].upper()}
                    • Sustainability Score: {data['sustainability_score']}/10
                    
                    {sustainability_note}
                    """
                }
    
    elif 'hello' in user_input or 'hi' in user_input:
        return {
            "response": "👋 Hello! I'm CryptoBuddy, your AI-powered financial sidekick!",
            "details": "I can help you find profitable and sustainable cryptocurrencies. Try asking me about:\n• Profitable coins 📈\n• Sustainable coins 🌱\n• Balanced recommendations ⚖️\n• Specific coins like Bitcoin or Ethereum"
        }
    
    elif 'help' in user_input:
        return {
            "response": "💬 I can help you with:",
            "details": """
            **Available Commands:**
            • **Profitable coins** - Find trending cryptocurrencies
            • **Sustainable/Eco-friendly** - Find green cryptocurrencies  
            • **Balanced recommendations** - Best overall options
            • **Coin info** - Ask about Bitcoin, Ethereum, Cardano, etc.
            • **Help** - Show this help message
            """
        }
    
    else:
        return {
            "response": "🤔 I'm not sure I understand. Try asking me about:",
            "details": "• **Profitable cryptocurrencies** 📈\n• **Sustainable/eco-friendly coins** 🌱\n• **Balanced investment options** ⚖️\n• **Specific coins** like Bitcoin or Ethereum\n• Or type **'help'** for more options"
        }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json['message']
    bot_response = process_message(user_message)
    
    return jsonify({
        'user_message': user_message,
        'bot_response': bot_response['response'],
        'details': bot_response.get('details', ''),
        'timestamp': datetime.datetime.now().strftime("%H:%M")
    })

if __name__ == '__main__':
    app.run(debug=True)