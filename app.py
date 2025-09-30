from flask import Flask, render_template, request, jsonify
import datetime
import requests
import re
import nltk
from textblob import TextBlob
import json

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

app = Flask(__name__)

# CoinGecko API configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINS_LIST = ["bitcoin", "ethereum", "cardano", "solana", "polkadot", "ripple", "dogecoin", "litecoin"]

class CryptoAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def get_coin_data(self, coin_id):
        """Get real-time data from CoinGecko API"""
        current_time = datetime.datetime.now().timestamp()
        
        # Check cache
        if coin_id in self.cache:
            cached_data, timestamp = self.cache[coin_id]
            if current_time - timestamp < self.cache_timeout:
                return cached_data
        
        try:
            # Get coin data from CoinGecko
            url = f"{COINGECKO_API_URL}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Process the data
            processed_data = {
                'name': data['name'],
                'symbol': data['symbol'].upper(),
                'current_price': data['market_data']['current_price']['usd'],
                'price_change_24h': data['market_data']['price_change_24h'],
                'price_change_percentage_24h': data['market_data']['price_change_percentage_24h'],
                'market_cap': data['market_data']['market_cap']['usd'],
                'market_cap_rank': data['market_data']['market_cap_rank'],
                'total_volume': data['market_data']['total_volume']['usd'],
                'high_24h': data['market_data']['high_24h']['usd'],
                'low_24h': data['market_data']['low_24h']['usd']
            }
            
            # Cache the data
            self.cache[coin_id] = (processed_data, current_time)
            return processed_data
            
        except Exception as e:
            print(f"Error fetching data for {coin_id}: {e}")
            return None
    
    def get_all_coins_data(self):
        """Get data for all tracked coins"""
        coins_data = {}
        for coin_id in COINS_LIST:
            data = self.get_coin_data(coin_id)
            if data:
                coins_data[coin_id] = data
        return coins_data
    
    def calculate_sustainability_score(self, coin_id):
        """Calculate sustainability score based on various factors"""
        # Predefined sustainability scores (in a real app, you'd use more sophisticated metrics)
        sustainability_scores = {
            "cardano": 8,
            "polkadot": 9,
            "solana": 7,
            "ethereum": 6,  # After merge
            "litecoin": 5,
            "bitcoin": 3,
            "ripple": 4,
            "dogecoin": 3
        }
        return sustainability_scores.get(coin_id, 5)
    
    def analyze_profitability(self, coins_data):
        """Analyze which coins are most profitable"""
        profitable_coins = []
        
        for coin_id, data in coins_data.items():
            price_change = data['price_change_percentage_24h']
            market_cap_rank = data['market_cap_rank']
            
            # Score based on price change and market cap
            if price_change > 0:  # Any positive growth
                score = price_change + (50 - min(market_cap_rank, 50))  # Prefer top 50 coins
                profitable_coins.append((coin_id, data, score))
        
        # Sort by profitability score
        profitable_coins.sort(key=lambda x: x[2], reverse=True)
        return profitable_coins
    
    def analyze_sustainability(self, coins_data):
        """Analyze which coins are most sustainable"""
        sustainable_coins = []
        
        for coin_id, data in coins_data.items():
            sustainability_score = self.calculate_sustainability_score(coin_id)
            
            if sustainability_score >= 6:  # Moderately sustainable coins
                score = sustainability_score + (data['price_change_percentage_24h'] / 10)  # Consider some growth
                sustainable_coins.append((coin_id, data, score, sustainability_score))
        
        # Sort by sustainability score
        sustainable_coins.sort(key=lambda x: x[2], reverse=True)
        return sustainable_coins

class NLProcessor:
    def __init__(self):
        self.keywords = {
            'profit': ['profit', 'money', 'gain', 'earn', 'make money', 'trending', 'rising', 'bullish'],
            'sustainability': ['sustainable', 'eco', 'green', 'environment', 'energy', 'carbon', 'footprint'],
            'balanced': ['balanced', 'best', 'recommend', 'advice', 'suggest', 'what should', 'which one'],
            'price': ['price', 'cost', 'value', 'how much', 'current price'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'better'],
            'help': ['help', 'what can you do', 'commands', 'options']
        }
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of the user input"""
        blob = TextBlob(text)
        return blob.sentiment.polarity  # -1 to 1
    
    def extract_entities(self, text):
        """Extract cryptocurrency names and other entities from text"""
        text_lower = text.lower()
        entities = {
            'cryptos': [],
            'intent': None,
            'urgency': 'normal'
        }
        
        # Extract cryptocurrency mentions
        crypto_patterns = {
            'bitcoin': ['bitcoin', 'btc'],
            'ethereum': ['ethereum', 'eth'],
            'cardano': ['cardano', 'ada'],
            'solana': ['solana', 'sol'],
            'polkadot': ['polkadot', 'dot'],
            'ripple': ['ripple', 'xrp'],
            'dogecoin': ['dogecoin', 'doge'],
            'litecoin': ['litecoin', 'ltc']
        }
        
        for crypto, patterns in crypto_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                entities['cryptos'].append(crypto)
        
        # Determine intent
        sentiment = self.analyze_sentiment(text)
        
        for intent_type, keywords in self.keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                entities['intent'] = intent_type
                break
        
        # Detect urgency
        urgent_words = ['now', 'immediately', 'urgent', 'asap', 'quick']
        if any(word in text_lower for word in urgent_words) or sentiment < -0.3:
            entities['urgency'] = 'high'
        elif sentiment > 0.5:
            entities['urgency'] = 'positive'
        
        return entities
    
    def generate_response_pattern(self, entities, coins_data):
        """Generate appropriate response based on extracted entities"""
        if not entities['intent'] and not entities['cryptos']:
            return self.get_help_response()
        
        intent = entities['intent']
        mentioned_cryptos = entities['cryptos']
        
        if intent == 'profit' or (not intent and any(word in ['rising', 'trending', 'up'] for word in entities.get('words', []))):
            return self.handle_profitability_query(coins_data, mentioned_cryptos)
        elif intent == 'sustainability':
            return self.handle_sustainability_query(coins_data, mentioned_cryptos)
        elif intent == 'balanced' or (not intent and not mentioned_cryptos):
            return self.handle_balanced_query(coins_data)
        elif intent == 'price' or mentioned_cryptos:
            return self.handle_price_query(coins_data, mentioned_cryptos)
        elif intent == 'comparison':
            return self.handle_comparison_query(coins_data, mentioned_cryptos)
        elif intent == 'help':
            return self.get_help_response()
        
        return self.get_fallback_response()
    
    def handle_profitability_query(self, coins_data, mentioned_cryptos):
        analyzer = CryptoAnalyzer()
        profitable_coins = analyzer.analyze_profitability(coins_data)
        
        if not profitable_coins:
            return {
                "response": "📊 Current Market Analysis",
                "details": "The market is showing mixed signals. Consider these stable options:\n\n" + 
                          self._format_coins_list(coins_data, limit=3)
            }
        
        best_coin_id, best_data, score = profitable_coins[0]
        sustainability_score = analyzer.calculate_sustainability_score(best_coin_id)
        
        emoji = "🚀" if best_data['price_change_percentage_24h'] > 5 else "📈"
        
        return {
            "response": f"{emoji} Top Performing: **{best_data['name']} ({best_data['symbol']})**",
            "details": f"""
            **Performance Metrics:**
            • Current Price: ${best_data['current_price']:,.2f}
            • 24h Change: {best_data['price_change_percentage_24h']:+.2f}%
            • Market Cap Rank: #{best_data['market_cap_rank']}
            • Sustainability Score: {sustainability_score}/10
            
            💡 **Insight:** Showing strong momentum with {best_data['price_change_percentage_24h']:+.2f}% growth.
            ⚠️ **Note:** Past performance doesn't guarantee future results.
            """
        }
    
    def handle_sustainability_query(self, coins_data, mentioned_cryptos):
        analyzer = CryptoAnalyzer()
        sustainable_coins = analyzer.analyze_sustainability(coins_data)
        
        if not sustainable_coins:
            return {
                "response": "🌱 Sustainable Options",
                "details": self._format_coins_list(coins_data, limit=5)
            }
        
        best_coin_id, best_data, score, sustainability = sustainable_coins[0]
        
        return {
            "response": f"🌿 Most Sustainable: **{best_data['name']} ({best_data['symbol']})**",
            "details": f"""
            **Eco-Friendly Metrics:**
            • Sustainability Score: {sustainability}/10 ⭐
            • Current Price: ${best_data['current_price']:,.2f}
            • 24h Performance: {best_data['price_change_percentage_24h']:+.2f}%
            • Market Position: #{best_data['market_cap_rank']}
            
            🌍 **Environmental Impact:** Energy-efficient consensus mechanism
            💚 **Green Choice:** Ideal for environmentally conscious investors
            """
        }
    
    def handle_balanced_query(self, coins_data):
        analyzer = CryptoAnalyzer()
        all_coins = []
        
        for coin_id, data in coins_data.items():
            sustainability = analyzer.calculate_sustainability_score(coin_id)
            profit_score = min(max(data['price_change_percentage_24h'], 0) + 5, 10)  # Normalize profit score
            balanced_score = (sustainability * 0.6) + (profit_score * 0.4)  # Weight sustainability more
            
            all_coins.append((coin_id, data, balanced_score, sustainability))
        
        all_coins.sort(key=lambda x: x[2], reverse=True)
        
        if not all_coins:
            return self.get_fallback_response()
        
        best_coin_id, best_data, score, sustainability = all_coins[0]
        
        return {
            "response": f"⚖️ Balanced Pick: **{best_data['name']} ({best_data['symbol']})**",
            "details": f"""
            **Balanced Analysis:**
            • Combined Score: {score:.1f}/10
            • Sustainability: {sustainability}/10
            • Profit Potential: {best_data['price_change_percentage_24h']:+.2f}%
            • Current Price: ${best_data['current_price']:,.2f}
            • Market Rank: #{best_data['market_cap_rank']}
            
            🎯 **Why This Choice:** Good balance of growth and responsibility
            📊 **Risk Level:** Moderate
            """
        }
    
    def handle_price_query(self, coins_data, mentioned_cryptos):
        if not mentioned_cryptos:
            # Show all prices if no specific crypto mentioned
            return {
                "response": "💰 Current Crypto Prices",
                "details": self._format_coins_list(coins_data, limit=8)
            }
        else:
            # Show specific crypto prices
            details = []
            for crypto in mentioned_cryptos:
                if crypto in coins_data:
                    data = coins_data[crypto]
                    sustainability = CryptoAnalyzer().calculate_sustainability_score(crypto)
                    change_emoji = "🟢" if data['price_change_percentage_24h'] > 0 else "🔴"
                    details.append(f"""
{change_emoji} **{data['name']} ({data['symbol']})**
• Current Price: ${data['current_price']:,.2f}
• 24h Change: {data['price_change_percentage_24h']:+.2f}%
• Market Cap: ${data['market_cap']:,.0f}
• Market Rank: #{data['market_cap_rank']}
• Sustainability: {sustainability}/10
                    """)
            
            if details:
                return {
                    "response": f"📊 Price Information",
                    "details": "\n".join(details)
                }
        
        return self.get_fallback_response()
    
    def handle_comparison_query(self, coins_data, mentioned_cryptos):
        if len(mentioned_cryptos) < 2:
            return {
                "response": "🔍 Comparison Request",
                "details": "Please mention at least two cryptocurrencies to compare. For example: 'Compare Bitcoin and Ethereum'"
            }
        
        analyzer = CryptoAnalyzer()
        comparison_data = []
        
        for crypto in mentioned_cryptos[:3]:  # Compare max 3 coins
            if crypto in coins_data:
                data = coins_data[crypto]
                sustainability = analyzer.calculate_sustainability_score(crypto)
                comparison_data.append((crypto, data, sustainability))
        
        if len(comparison_data) < 2:
            return self.get_fallback_response()
        
        comparison_text = ["**Side-by-Side Comparison:**"]
        for crypto, data, sustainability in comparison_data:
            change_emoji = "🟢" if data['price_change_percentage_24h'] > 0 else "🔴"
            comparison_text.append(f"""
{change_emoji} **{data['name']} ({data['symbol']})**
• Price: ${data['current_price']:,.2f}
• 24h Change: {data['price_change_percentage_24h']:+.2f}%
• Market Cap: #{data['market_cap_rank']}
• Sustainability: {sustainability}/10
• Volume: ${data['total_volume']:,.0f}
            """)
        
        return {
            "response": "⚔️ Crypto Comparison",
            "details": "\n".join(comparison_text)
        }
    
    def _format_coins_list(self, coins_data, limit=5):
        """Format a list of coins for display"""
        coins_list = []
        count = 0
        
        for coin_id, data in coins_data.items():
            if count >= limit:
                break
            change_emoji = "🟢" if data['price_change_percentage_24h'] > 0 else "🔴"
            coins_list.append(f"{change_emoji} {data['name']}: ${data['current_price']:,.2f} ({data['price_change_percentage_24h']:+.2f}%)")
            count += 1
        
        return "\n".join(coins_list)
    
    def get_help_response(self):
        return {
            "response": "💬 CryptoBuddy Pro Help Center",
            "details": """
**I understand natural language! Try asking me:**

📈 **Profit & Growth:**
• "Which crypto is making money?"
• "Show me trending coins"
• "What's profitable right now?"

🌱 **Sustainability:**
• "Find eco-friendly cryptocurrencies"
• "Which coins are green?"
• "Show me sustainable options"

⚖️ **Balanced Advice:**
• "What should I invest in?"
• "Give me a balanced recommendation"
• "Best crypto for long-term"

💰 **Price Information:**
• "What's Bitcoin's price?"
• "How much is Ethereum?"
• "Show me current prices"

🔍 **Comparisons:**
• "Compare Bitcoin and Ethereum"
• "Which is better: Cardano or Solana?"

💡 **Pro Tip:** I use real-time data from CoinGecko API!
            """
        }
    
    def get_fallback_response(self):
        return {
            "response": "🤔 I want to help, but I'm not sure what you're looking for.",
            "details": "Try asking about:\n• Profitable cryptocurrencies 📈\n• Sustainable/eco-friendly coins 🌱\n• Price information 💰\n• Comparisons between coins ⚔️\nOr type 'help' for more options!"
        }

# Initialize our components
crypto_analyzer = CryptoAnalyzer()
nl_processor = NLProcessor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json['message']
    
    # Get real-time data
    coins_data = crypto_analyzer.get_all_coins_data()
    
    # Process with NLP
    entities = nl_processor.extract_entities(user_message)
    bot_response = nl_processor.generate_response_pattern(entities, coins_data)
    
    return jsonify({
        'user_message': user_message,
        'bot_response': bot_response['response'],
        'details': bot_response.get('details', ''),
        'timestamp': datetime.datetime.now().strftime("%H:%M"),
        'entities': entities  # For debugging
    })

@app.route('/market_data')
def market_data():
    """API endpoint to get current market data"""
    coins_data = crypto_analyzer.get_all_coins_data()
    return jsonify(coins_data)

if __name__ == '__main__':
    print("🚀 Starting CryptoBuddy Pro...")
    print("📊 Loading real-time market data...")
    print("🌐 Server will be available at: http://localhost:5000")
    app.run(debug=True)