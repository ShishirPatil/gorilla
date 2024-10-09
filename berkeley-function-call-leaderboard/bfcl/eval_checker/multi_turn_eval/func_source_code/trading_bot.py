from datetime import datetime, time
from typing import Dict, List, Optional, Union

from .long_context import (
    AUTOMOBILE_EXTENSION,
    MA_5_EXTENSION,
    MA_20_EXTENSION,
    ORDER_DETAIL_EXTENSION,
    TECHNOLOGY_EXTENSION,
    TRANSACTION_HISTORY_EXTENSION,
    WATCH_LIST_EXTENSION,
)


class TradingBot:
    """
    A class representing a trading bot for executing stock trades and managing a trading account.

    Attributes:
        orders (Dict[int, Dict[str, Union[str, float, int]]]): A dictionary of orders, keyed by order ID.
        account_info (Dict[str, Union[int, float]]): Information about the trading account.
        authenticated (bool): Whether the user is currently authenticated.
        market_status (str): The current status of the market ('Open' or 'Closed').
        order_counter (int): A counter for generating unique order IDs.
        stocks (Dict[str, Dict[str, Union[float, int]]]): Information about various stocks.
        watch_list (List[str]): A list of stock symbols being watched.
        transaction_history (List[Dict[str, Union[str, float, int]]]): A history of transactions.
    """

    def __init__(self):
        """
        Initialize the TradingBot instance.
        """
        self.orders: Dict[int, Dict[str, Union[str, float, int]]]
        self.account_info: Dict[str, Union[int, float]]
        self.authenticated: bool
        self.market_status: str
        self.order_counter: int
        self.stocks: Dict[str, Dict[str, Union[float, int]]]
        self.watch_list: List[str]
        self.transaction_history: List[Dict[str, Union[str, float, int]]]

    def _load_scenario(self, scenario: dict, long_context=False) -> None:
        """
        Load a scenario into the TradingBot.

        Args:
            scenario (dict): A scenario dictionary containing data to load.
        """
        self.orders = scenario.get("orders", {
            12345: {
            "symbol": "AAPL",
            "price": 210.65,
            "num_shares": 10,
            "status": "Completed",
            },
            12446: {
                "symbol": "GOOG",
                "price": 2840.56,
                "num_shares": 5,
                "status": "Pending",
            }
        })
        # Convert all string keys that can be interpreted as integers to integer keys
        self.orders = {int(k) if isinstance(k, str) and k.isdigit() else k: v for k, v in self.orders.items()}
        self.account_info = scenario.get("account_info", {
            "account_id": 12345,
            "balance": 10000.0,
            "binding_card": 1974202140965533,
        })
        self.authenticated = scenario.get("authenticated", False)
        self.market_status = scenario.get("market_status", "Closed")
        self.order_counter = scenario.get("order_counter", 12446) # Start counter from the next order ID
        self.stocks = scenario.get("stocks", {
            "AAPL": {
                "price": 227.16,
                "percent_change": 0.17,
                "volume": 2.552,
                "MA(5)": 227.11,
                "MA(20)": 227.09,
            },
            "GOOG": {
                "price": 2840.34,
                "percent_change": 0.24,
                "volume": 1.123,
                "MA(5)": 2835.67,
                "MA(20)": 2842.15,
            },
            "TSLA": {
                "price": 667.92,
                "percent_change": -0.12,
                "volume": 1.654,
                "MA(5)": 671.15,
                "MA(20)": 668.20,
            },
            "MSFT": {
                "price": 310.23,
                "percent_change": 0.09,
                "volume": 3.234,
                "MA(5)": 309.88,
                "MA(20)": 310.11,
            },
            "NVDA": {
                "price": 220.34,
                "percent_change": 0.34,
                "volume": 1.234,
                "MA(5)": 220.45,
                "MA(20)": 220.67,
            },
            "ALPH": {
                "price": 1320.45,
                "percent_change": -0.08,
                "volume": 1.567,
                "MA(5)": 1321.12,
                "MA(20)": 1325.78,
            },
            "OMEG": {
                "price": 457.23,
                "percent_change": 0.12,
                "volume": 2.345,
                "MA(5)": 456.78,
                "MA(20)": 458.12,
            },
            "QUAS": {
                "price": 725.89,
                "percent_change": -0.03,
                "volume": 1.789,
                "MA(5)": 726.45,
                "MA(20)": 728.00,
            },
            "NEPT": {
                "price": 88.34,
                "percent_change": 0.19,
                "volume": 0.654,
                "MA(5)": 88.21,
                "MA(20)": 88.67,
            },
            "SYNX": {
                "price": 345.67,
                "percent_change": 0.11,
                "volume": 2.112,
                "MA(5)": 345.34,
                "MA(20)": 346.12,
            },
            "ZETA": {
                "price": 22.09,
                "percent_change": -0.05,
                "volume": 0.789,
                "MA(5)": 22.12,
                "MA(20)": 22.34,
            },
        })
        self.watch_list = scenario.get("watch_list", ["NVDA"])
        self.transaction_history = scenario.get("transaction_history", [])
        self.long_context = long_context

    def get_current_time(self) -> str:
        """
        Get the current time.

        Returns:
            current_time (str): Current time in HH:MM AM/PM format.
        """
        current_time = datetime(2024, 9, 1, 10, 30)
        return current_time.strftime("%I:%M %p")

    def update_market_status(self, current_time_str: str) -> Dict[str, str]:
        """
        Update the market status based on the current time.

        Args:
            current_time_str (str): Current time in HH:MM AM/PM format.

        Returns:
            status (str): Status of the market ('Open' or 'Closed').
        """
        market_open_time = time(9, 30)  # Market opens at 9:30 AM
        market_close_time = time(16, 0)  # Market closes at 4:00 PM

        current_time = datetime.strptime(current_time_str, "%I:%M %p").time()

        if market_open_time <= current_time <= market_close_time:
            self.market_status = "Open"
            return {"status": "Open"}
        else:
            self.market_status = "Closed"
            return {"status": "Closed"}

    def get_symbol_by_name(self, name: str) -> str:
        """
        Get the symbol of a stock by company name.

        Args:
            name (str): Name of the company.

        Returns:
            symbol (str): Symbol of the stock or "Stock not found" if not available.
        """
        symbol_map = {
            "Apple": "AAPL",
            "Google": "GOOG",
            "Tesla": "TSLA",
            "Microsoft": "MSFT",
            "Nvidia": "NVDA",
            "Zeta Corp": "ZETA",
            "Alpha Tech": "ALPH",
            "Omega Industries": "OMEG",
            "Quasar Ltd.": "QUAS",
            "Neptune Systems": "NEPT",
            "Synex Solutions": "SYNX",
            "Amazon": "AMZN",
        }

        return symbol_map.get(name, "Stock not found")

    def get_stock_info(self, symbol: str) -> Dict[str, Union[float, int, str]]:
        """
        Get the details of a stock.

        Args:
            symbol (str): Symbol that uniquely identifies the stock.

        Returns:
            price (float): Current price of the stock.
            percent_change (float): Percentage change in stock price.
            volume (float): Trading volume of the stock.
            MA5 (float): 5-day Moving Average of the stock.
            MA20 (float): 20-day Moving Average of the stock.
        """
        if symbol not in self.stocks:
            return {"error": f"Stock with symbol '{symbol}' not found."}
        if self.long_context:
            stock = self.stocks[symbol].copy()
            stock["MA(5)"] = MA_5_EXTENSION
            stock["MA(20)"] = MA_20_EXTENSION
            return stock
        return self.stocks[symbol]

    def get_order_details(self, order_id: int) -> Dict[str, Union[str, float, int]]:
        """
        Get the details of an order.

        Args:
            order_id (int): ID of the order.

        Returns:
            symbol (str): Symbol of the stock in the order.
            price (float): Price at which the order was placed.
            num_shares (int): Number of shares in the order.
            status (str): Current status of the order.
        """
        if order_id not in self.orders:
            return {
                "error": f"Order with ID {order_id} not found."
                + "Here is the list of orders_id: "
                + str(list(self.orders.keys()))
            }

        if self.long_context:
            order = self.orders[order_id].copy()
            symbol = order["symbol"]

            formatted_extension = {}
            for key, value in ORDER_DETAIL_EXTENSION.items():
                try:
                    formatted_extension[key] = value.format(symbol=symbol)
                except KeyError as e:
                    return {"error": f"KeyError during formatting: {str(e)}"}

            # Add formatted extension to the order metadata
            order["metadata"] = formatted_extension
            return order

        return self.orders[order_id]

    def cancel_order(self, order_id: int) -> Dict[str, Union[int, str]]:
        """
        Cancel an order.

        Args:
            order_id (int): ID of the order to cancel.

        Returns:
            order_id (int): ID of the cancelled order.
            status (str): New status of the order after cancellation attempt.
        """
        if order_id not in self.orders:
            return {"error": f"Order with ID {order_id} not found."}
        if self.orders[order_id]["status"] == "Completed":
            return {"error": f"Can't cancel order {order_id}. Order is already completed."}
        self.orders[order_id]["status"] = "Cancelled"
        return {"order_id": order_id, "status": "Cancelled"}

    def place_order(
        self, order_type: str, symbol: str, price: float, amount: int
    ) -> Dict[str, Union[int, str, float]]:
        """
        Place an order.

        Args:
            order_type (str): Type of the order (Buy/Sell).
            symbol (str): Symbol of the stock to trade.
            price (float): Price at which to place the order.
            amount (int): Number of shares to trade.

        Returns:
            order_id (int): ID of the newly placed order.
            order_type (str): Type of the order (Buy/Sell).
            status (str): Initial status of the order.
            price (float): Price at which the order was placed.
            amount (int): Number of shares in the order.
        """
        if not self.authenticated:
            return {"error": "User not authenticated. Please log in to place an order."}
        if symbol not in self.stocks:
            return {"error": f"Invalid stock symbol: {symbol}"}
        if price <= 0 or amount <= 0:
            return {"error": "Price and amount must be positive values."}

        order_id = self.order_counter
        self.orders[order_id] = {
            "order_type": order_type,
            "symbol": symbol,
            "price": price,
            "amount": amount,
            "status": "Open",
        }
        self.order_counter += 1
        return {
            "order_id": order_id,
            "order_type": order_type,
            "status": "Pending",
            "price": price,
            "amount": amount,
        }

    def make_transaction(
        self, account_id: int, xact_type: str, amount: float
    ) -> Dict[str, Union[str, float]]:
        """
        Make a deposit or withdrawal based on specified amount.

        Args:
            account_id (int): ID of the account.
            xact_type (str): Transaction type (deposit or withdrawal).
            amount (float): Amount to deposit or withdraw.

        Returns:
            status (str): Status of the transaction.
            new_balance (float): Updated account balance after the transaction.
        """
        if not self.authenticated:
            return {"error": "User not authenticated. Please log in to make a transaction."}
        if self.market_status != "Open":
            return {"error": "Market is closed. Transactions are not allowed."}
        if account_id != self.account_info["account_id"]:
            return {"error": f"Account with ID {account_id} not found."}
        if amount <= 0:
            return {"error": "Transaction amount must be positive."}

        if xact_type == "deposit":
            self.account_info["balance"] += amount
            self.transaction_history.append(
                {
                    "type": "deposit",
                    "amount": amount,
                    "timestamp": self.get_current_time(),
                }
            )
            return {
                "status": "Deposit successful",
                "new_balance": self.account_info["balance"],
            }
        elif xact_type == "withdrawal":
            if amount > self.account_info["balance"]:
                return {"error": "Insufficient funds for withdrawal."}
            self.account_info["balance"] -= amount
            self.transaction_history.append(
                {
                    "type": "withdrawal",
                    "amount": amount,
                    "timestamp": self.get_current_time(),
                }
            )
            return {
                "status": "Withdrawal successful",
                "new_balance": self.account_info["balance"],
            }
        return {"error": "Invalid transaction type. Use 'deposit' or 'withdrawal'."}

    def get_account_info(self) -> Dict[str, Union[int, float]]:
        """
        Get account information.

        Returns:
            account_id (int): ID of the account.
            balance (float): Current balance of the account.
            binding_card (int): Card number associated with the account.
        """
        if not self.authenticated:
            return {
                "error": "User not authenticated. Please log in to view account information."
            }
        return self.account_info

    def trading_login(self, username: str, password: str) -> Dict[str, str]:
        """
        Handle user login.

        Args:
            username (str): Username for authentication.
            password (str): Password for authentication.

        Returns:
            status (str): Login status message.
        """
        if self.authenticated:
            return {"status": "Already logged in"}
        # In a real system, we would validate the username and password here
        self.authenticated = True
        return {"status": "Logged in successfully"}

    def trading_logout(self) -> Dict[str, str]:
        """
        Handle user logout for trading system.

        Returns:
            status (str): Logout status message.
        """
        if not self.authenticated:
            return {"status": "No user is currently logged in"}
        self.authenticated = False
        return {"status": "Logged out successfully"}

    def fund_account(self, amount: float) -> Dict[str, Union[str, float]]:
        """
        Fund the account with the specified amount.

        Args:
            amount (float): Amount to fund the account with.

        Returns:
            status (str): Status of the funding operation.
            new_balance (float): Updated account balance after funding.
        """
        if not self.authenticated:
            return {"error": "User not authenticated. Please log in to fund the account."}
        if amount <= 0:
            return {"error": "Funding amount must be positive."}
        self.account_info["balance"] += amount
        self.transaction_history.append(
            {"type": "funding", "amount": amount, "timestamp": self.get_current_time()}
        )
        return {
            "status": "Account funded successfully",
            "new_balance": self.account_info["balance"],
        }


    def remove_stock_from_watchlist(self, symbol: str) -> Dict[str, str]:
        """
        Remove a stock from the watchlist.

        Args:
            symbol (str): Symbol of the stock to remove.

        Returns:
            status (str): Status of the removal operation.
        """
        if not self.authenticated:
            return {
                "error": "User not authenticated. Please log in to modify the watchlist."
            }
        if symbol not in self.watch_list:
            return {"error": f"Stock {symbol} not found in watchlist."}
        self.watch_list.remove(symbol)
        return {"status": f"Stock {symbol} removed from watchlist successfully."}

    def get_watchlist(self) -> List[str]:
        """
        Get the watchlist.

        Returns:
            watchlist (List[str]): List of stock symbols in the watchlist.
        """
        if not self.authenticated:
            return ["Error: User not authenticated. Please log in to view the watchlist."]

        if self.long_context:
            watch_list = self.watch_list.copy()
            watch_list.extend(WATCH_LIST_EXTENSION)
            return watch_list
        return self.watch_list

    def get_transaction_history(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Get the transaction history within a specified date range.

        Args:
            start_date (Optional[str]): Start date for the history (format: 'YYYY-MM-DD').
            end_date (Optional[str]): End date for the history (format: 'YYYY-MM-DD').

        Returns:
            history (List[Dict[str, str]]): List of transactions within the specified date range.
        """
        if not self.authenticated:
            return [
                {
                    "error": "User not authenticated. Please log in to view transaction history."
                }
            ]

        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start = datetime.min

        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end = datetime.max

        filtered_history = [
            transaction
            for transaction in self.transaction_history
            if start <= datetime.strptime(transaction["timestamp"], "%I:%M %p") <= end
        ]

        if self.long_context:
            filtered_history.extend(TRANSACTION_HISTORY_EXTENSION)

        return filtered_history

    def update_stock_price(
        self, symbol: str, new_price: float
    ) -> Dict[str, Union[str, float]]:
        """
        Update the price of a stock.

        Args:
            symbol (str): Symbol of the stock to update.
            new_price (float): New price of the stock.

        Returns:
            symbol (str): Symbol of the updated stock.
            old_price (float): Previous price of the stock.
            new_price (float): Updated price of the stock.
        """
        if symbol not in self.stocks:
            return {"error": f"Stock with symbol '{symbol}' not found."}
        if new_price <= 0:
            return {"error": "New price must be a positive value."}

        old_price = self.stocks[symbol]["price"]
        self.stocks[symbol]["price"] = new_price
        self.stocks[symbol]["percent_change"] = ((new_price - old_price) / old_price) * 100

        return {"symbol": symbol, "old_price": old_price, "new_price": new_price}

    # below contains a list of functions to be nested
    def get_available_stocks(self, sector: str) -> List[str]:
        """
        Get a list of stock symbols in the given sector.

        Args:
            sector (str): The sector to retrieve stocks from (e.g., 'Technology').

        Returns:
            stock_list (List[str]): List of stock symbols in the specified sector.
        """
        sector_map = {
            "Technology": ["AAPL", "GOOG", "MSFT", "NVDA"],
            "Automobile": ["TSLA", "F", "GM"],
        }

        if self.long_context:
            sector_map["Technology"].extend(TECHNOLOGY_EXTENSION)
            sector_map["Automobile"].extend(AUTOMOBILE_EXTENSION)
        return sector_map.get(sector, [])

    def filter_stocks_by_price(
        self, stocks: List[str], min_price: float, max_price: float
    ) -> List[str]:
        """
        Filter stocks based on a price range.

        Args:
            stocks (List[str]): List of stock symbols to filter.
            min_price (float): Minimum stock price.
            max_price (float): Maximum stock price.

        Returns:
            filtered_stocks (List[str]): Filtered list of stock symbols within the price range.
        """
        filtered_stocks = [
            symbol
            for symbol in stocks
            if self.stocks.get(symbol, {}).get("price", 0) >= min_price
            and self.stocks.get(symbol, {}).get("price", 0) <= max_price
        ]
        return filtered_stocks

    def add_to_watchlist(self, stocks: List[str]) -> List[str]:
        """
        Add a list of stocks to the watchlist.

        Args:
            stocks (List[str]): List of stock symbols to add to the watchlist.

        Returns:
            symbols (List[str]): List of stock symbols that were successfully added to the watchlist.
        """
        for symbol in stocks:
            if symbol not in self.watch_list:
                if symbol in self.stocks:  # Ensure symbol is valid
                    self.watch_list.append(symbol)
        return self.watch_list

    def notify_price_change(self, stocks: List[str], threshold: float) -> Dict[str, str]:
        """
        Notify if there is a significant price change in the stocks.

        Args:
            stocks (List[str]): List of stock symbols to check.
            threshold (float): Percentage change threshold to trigger a notification.

        Returns:
            notifications (Dict[str, str]): Notification message about the price changes.
        """
        changed_stocks = [
            symbol
            for symbol in stocks
            if symbol in self.stocks
            and abs(self.stocks[symbol]["percent_change"]) >= threshold
        ]

        if changed_stocks:
            return {
                "notification": f"Stocks {', '.join(changed_stocks)} have significant price changes."
            }
        else:
            return {"notification": "No significant price changes in the selected stocks."}
