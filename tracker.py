import bcrypt
import mysql.connector
from mysql.connector import Error
import yfinance as yf
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
from dotenv import load_dotenv
import time


load_dotenv()


class StockDataAPI:
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.use_alpha_vantage = False

    def toggle_api(self):

        self.use_alpha_vantage = not self.use_alpha_vantage
        source = "Alpha Vantage" if self.use_alpha_vantage else "Yahoo Finance"
        print(f"Switched to {source} for market data")
        return source

    def get_current_price(self, symbol):

        if self.use_alpha_vantage:
            return self._get_price_alpha_vantage(symbol)
        else:
            return self._get_price_yfinance(symbol)

    def _get_price_yfinance(self, symbol):

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return hist['Close'].iloc[-1]
            return None
        except Exception as e:
            print(f"YFinance Error for {symbol}: {str(e)}")
            return None

    def _get_price_alpha_vantage(self, symbol):

        if not self.alpha_vantage_key:
            print("Alpha Vantage API key not configured")
            return None

        base_url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                return float(data['Global Quote']['05. price'])
            else:
                error_msg = data.get('Note', data.get('Information', 'Unknown error'))
                print(f"AlphaVantage Error for {symbol}: {error_msg}")
                return None
        except Exception as e:
            print(f"AlphaVantage Connection Error: {str(e)}")
            return None


class MySQLPortfolioDB:
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.database = os.getenv('MYSQL_DATABASE', 'stock_portfolio_tracker')
        self.user = os.getenv('MYSQL_USER', 'portfolio_user')
        self.raw_password = os.getenv('MYSQL_PASSWORD', '')
        self._init_db()

    def _hash_password(self, password):

        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def _verify_password(self, stored_hash, provided_password):

        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash)

    def _get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.raw_password
            )
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    def _init_db(self):

        connection = self._get_connection()
        if connection:
            try:
                cursor = connection.cursor()


                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                cursor.execute(f"USE {self.database}")


                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                e
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        symbol VARCHAR(10) NOT NULL,
                        shares DECIMAL(15, 4) NOT NULL,
                        purchase_price DECIMAL(15, 4) NOT NULL,
                        purchase_date DATE NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE KEY user_symbol (user_id, symbol)
                    )
                ''')

                connection.commit()
            except Error as e:
                print(f"Error initializing database: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()

    def create_user(self, username, password):

        hashed_pw = self._hash_password(password)
        connection = self._get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s)
                ''', (username, hashed_pw))
                connection.commit()
                return cursor.lastrowid
            except Error as e:
                print(f"Error creating user: {e}")
                return None
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        return None

    def authenticate_user(self, username, password):

        connection = self._get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, password_hash FROM users WHERE username = %s
                ''', (username,))
                result = cursor.fetchone()

                if result and self._verify_password(result['password_hash'], password):
                    return result['id']
                return None
            except Error as e:
                print(f"Error authenticating user: {e}")
                return None
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        return None

    def save_portfolio(self, user_id, portfolio):

        connection = self._get_connection()
        if connection:
            try:
                cursor = connection.cursor()


                cursor.execute("DELETE FROM portfolio WHERE user_id = %s", (user_id,))


                for symbol, data in portfolio.items():
                    cursor.execute('''
                        INSERT INTO portfolio (user_id, symbol, shares, purchase_price, purchase_date)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (user_id, symbol, data['shares'], data['purchase_price'], data['purchase_date']))

                connection.commit()
                return True
            except Error as e:
                print(f"Error saving portfolio: {e}")
                return False
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        return False

    def load_portfolio(self, user_id):
        """Load user's portfolio from database"""
        portfolio = {}
        connection = self._get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute('''
                    SELECT symbol, shares, purchase_price, purchase_date 
                    FROM portfolio WHERE user_id = %s
                ''', (user_id,))

                for row in cursor:
                    portfolio[row['symbol']] = {
                        'shares': float(row['shares']),
                        'purchase_price': float(row['purchase_price']),
                        'purchase_date': row['purchase_date'].strftime('%Y-%m-%d')
                    }

                return portfolio
            except Error as e:
                print(f"Error loading portfolio: {e}")
                return {}
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        return {}


class StockPortfolioTracker:
    def __init__(self):
        self.db = MySQLPortfolioDB()
        self.api = StockDataAPI()
        self.current_user_id = None
        self.current_username = None
        self.portfolio = {}

    def register(self):
        """Handle user registration"""
        print("\n=== Registration ===")
        username = input("Choose a username: ").strip()
        password = input("Choose a password: ").strip()

        if not username or not password:
            print("Username and password cannot be empty")
            return False

        user_id = self.db.create_user(username, password)
        if user_id:
            print("Registration successful! Please login.")
            return True
        else:
            print("Registration failed. Username may already exist.")
            return False

    def login(self):
        """Handle user login"""
        print("\n=== Login ===")
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        user_id = self.db.authenticate_user(username, password)
        if user_id:
            self.current_user_id = user_id
            self.current_username = username
            self.portfolio = self.db.load_portfolio(user_id)
            print(f"\nWelcome back, {username}!")
            return True
        else:
            print("Invalid credentials")
            return False

    def logout(self):
        """Handle user logout"""
        self.current_user_id = None
        self.current_username = None
        self.portfolio = {}
        print("Logged out successfully")

    def add_stock(self, symbol, shares, purchase_price, purchase_date):
        """Add or update a stock in the portfolio"""
        symbol = symbol.upper()
        try:
            shares = float(shares)
            purchase_price = float(purchase_price)
            datetime.strptime(purchase_date, "%Y-%m-%d")  
        except ValueError as e:
            print(f"Invalid input: {e}")
            return

        if symbol in self.portfolio:
            
            total_shares = self.portfolio[symbol]['shares'] + shares
            total_cost = (self.portfolio[symbol]['shares'] * self.portfolio[symbol]['purchase_price']) + (
                        shares * purchase_price)
            self.portfolio[symbol]['purchase_price'] = total_cost / total_shares
            self.portfolio[symbol]['shares'] = total_shares
            print(
                f"Updated {symbol} position to {total_shares} shares at avg price ${self.portfolio[symbol]['purchase_price']:.2f}")
        else:
            self.portfolio[symbol] = {
                'shares': shares,
                'purchase_price': purchase_price,
                'purchase_date': purchase_date
            }
            print(f"Added {shares} shares of {symbol} to portfolio")

        self.db.save_portfolio(self.current_user_id, self.portfolio)

    def remove_stock(self, symbol, shares=None):
        """Remove all or partial shares of a stock"""
        symbol = symbol.upper()
        if symbol not in self.portfolio:
            print(f"{symbol} not in portfolio")
            return

        if shares is None or shares >= self.portfolio[symbol]['shares']:
            del self.portfolio[symbol]
            print(f"Removed all shares of {symbol}")
        else:
            self.portfolio[symbol]['shares'] -= shares
            print(f"Removed {shares} shares of {symbol}. Remaining: {self.portfolio[symbol]['shares']}")

        self.db.save_portfolio(self.current_user_id, self.portfolio)

    def portfolio_summary(self):
        """Generate detailed portfolio report"""
        if not self.portfolio:
            print("Portfolio is empty")
            return

        total_investment = 0
        total_current_value = 0
        report = []

        for symbol, data in self.portfolio.items():
            current_price = self.api.get_current_price(symbol)
            if current_price is None:
                print(f"Could not get price for {symbol}")
                continue

            shares = data['shares']
            cost_basis = data['purchase_price']
            investment = shares * cost_basis
            current_value = shares * current_price
            gain_loss = current_value - investment
            gain_loss_pct = (gain_loss / investment) * 100

            total_investment += investment
            total_current_value += current_value

            report.append({
                'Symbol': symbol,
                'Shares': f"{shares:.2f}",
                'Avg Cost': f"${cost_basis:.2f}",
                'Current Price': f"${current_price:.2f}",
                'Invested': f"${investment:.2f}",
                'Current Value': f"${current_value:.2f}",
                'Gain/Loss ($)': f"${gain_loss:.2f}",
                'Gain/Loss (%)': f"{gain_loss_pct:.2f}%"
            })


        total_gain_loss = total_current_value - total_investment
        total_gain_loss_pct = (total_gain_loss / total_investment) * 100 if total_investment != 0 else 0


        df = pd.DataFrame(report)
        print("\n=== PORTFOLIO DETAILS ===")
        print(df.to_string(index=False))

        print("\n=== SUMMARY ===")
        print(f"Total Invested: ${total_investment:.2f}")
        print(f"Current Value: ${total_current_value:.2f}")
        print(f"Total Gain/Loss: ${total_gain_loss:.2f} ({total_gain_loss_pct:.2f}%)")

    def plot_portfolio(self):
        """Visualize portfolio distribution"""
        if not self.portfolio:
            print("Portfolio is empty")
            return

        symbols = []
        values = []

        for symbol, data in self.portfolio.items():
            current_price = self.api.get_current_price(symbol)
            if current_price is None:
                continue
            symbols.append(symbol)
            values.append(data['shares'] * current_price)

        if not values:
            print("No valid data to plot")
            return

        plt.figure(figsize=(10, 6))
        plt.pie(values, labels=symbols, autopct='%1.1f%%', startangle=90)
        plt.title(f'Portfolio Composition for {self.current_username}')
        plt.show()


def main():
    tracker = StockPortfolioTracker()

    # Authentication loop
    while True:
        print("\n===== Stock Portfolio Tracker =====")
        print("1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("Enter choice (1-3): ").strip()

        if choice == '1':
            if tracker.login():
                break  # Proceed to main menu
        elif choice == '2':
            tracker.register()
        elif choice == '3':
            print("Goodbye!")
            return
        else:
            print("Invalid choice")

    # Main application loop
    while True:
        print("\n===== Main Menu =====")
        print(f"Logged in as: {tracker.current_username}")
        print("1. Add/Update Stock")
        print("2. Remove Stock")
        print("3. View Portfolio")
        print("4. Plot Portfolio")
        print("5. Switch Data Source (Current: " +
              ("Alpha Vantage" if tracker.api.use_alpha_vantage else "Yahoo Finance") + ")")
        print("6. Logout")

        choice = input("Enter choice (1-6): ").strip()

        if choice == '1':
            try:
                symbol = input("Stock symbol: ").strip().upper()
                shares = float(input("Number of shares: ").strip())
                price = float(input("Purchase price per share: ").strip())
                date = input("Purchase date (YYYY-MM-DD): ").strip()
                tracker.add_stock(symbol, shares, price, date)
            except ValueError:
                print("Invalid input. Please enter valid numbers.")

        elif choice == '2':
            symbol = input("Stock symbol to remove: ").strip().upper()
            action = input("Remove all shares? (Y/N): ").strip().upper()
            if action == 'Y':
                tracker.remove_stock(symbol)
            else:
                try:
                    shares = float(input("Number of shares to remove: ").strip())
                    tracker.remove_stock(symbol, shares)
                except ValueError:
                    print("Invalid share amount")

        elif choice == '3':
            tracker.portfolio_summary()

        elif choice == '4':
            tracker.plot_portfolio()

        elif choice == '5':
            source = tracker.api.toggle_api()
            print(f"Now using {source} for market data")

        elif choice == '6':
            tracker.logout()
            break

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
