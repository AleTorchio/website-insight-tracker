import os
import sys
import time
import threading
from datetime import datetime, timedelta
import logging

# Auto-install dependencies if needed
packages = ['ccxt', 'pandas']
for package in packages:
    try:
        __import__(package)
    except ImportError:
        logging.info(f"Installing {package}...")
        os.system(f"{sys.executable} -m pip install {package} --quiet")

import ccxt
import pandas as pd
from app import app, db
from models import Exchange, PriceData, ArbitrageOpportunity, MonitoringStats

class CryptoMonitor:
    def __init__(self):
        self.exchanges_config = ['binance', 'kucoin', 'kraken', 'mexc']
        self.pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
        self.check_interval = 30  # seconds - check more frequently
        self.min_profit_threshold = 0.05  # 0.05% minimum - very low threshold to catch micro-opportunities
        self.exchanges = {}
        self.running = False
        
    def initialize_exchanges(self):
        """Initialize exchange connections"""
        with app.app_context():
            logging.info("Initializing exchanges...")
            
            for exchange_id in self.exchanges_config:
                try:
                    # Create exchange instance
                    exchange_class = getattr(ccxt, exchange_id)
                    exchange = exchange_class({
                        'enableRateLimit': True,
                        'timeout': 10000,
                        'sandbox': False
                    })
                    
                    # Test connection
                    exchange.load_markets()
                    self.exchanges[exchange_id] = exchange
                    
                    # Store/update in database
                    db_exchange = Exchange.query.filter_by(name=exchange_id).first()
                    if not db_exchange:
                        db_exchange = Exchange(name=exchange_id, status='active', last_check=datetime.utcnow())
                        db.session.add(db_exchange)
                    
                    db_exchange.status = 'active'
                    db_exchange.last_check = datetime.utcnow()
                    
                    logging.info(f"✅ {exchange_id.upper()} connected")
                    
                except Exception as e:
                    logging.warning(f"❌ {exchange_id.upper()} failed: {e}")
                    
                    # Update database status
                    db_exchange = Exchange.query.filter_by(name=exchange_id).first()
                    if not db_exchange:
                        db_exchange = Exchange(name=exchange_id, status='inactive', last_check=datetime.utcnow())
                        db.session.add(db_exchange)
                    
                    db_exchange.status = 'inactive'
                    db_exchange.last_check = datetime.utcnow()
            
            db.session.commit()
            logging.info(f"🔥 {len(self.exchanges)} exchanges ready!")
    
    def get_prices(self):
        """Fetch prices from all exchanges"""
        all_prices = {}
        
        for symbol in self.pairs:
            all_prices[symbol] = {}
            
            for name, exchange in self.exchanges.items():
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    price_data = {
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'last': ticker['last'],
                        'volume': ticker['quoteVolume']
                    }
                    all_prices[symbol][name] = price_data
                    
                    # Save to database
                    with app.app_context():
                        db_exchange = Exchange.query.filter_by(name=name).first()
                        if db_exchange and price_data['last']:
                            price_record = PriceData(
                                symbol=symbol,
                                exchange_id=db_exchange.id,
                                price=price_data['last'],
                                bid=price_data['bid'],
                                ask=price_data['ask'],
                                volume=price_data['volume'] or 0
                            )
                            db.session.add(price_record)
                        
                        # Update exchange last check
                        db_exchange.last_check = datetime.utcnow()
                        db_exchange.status = 'active'
                        
                except Exception as e:
                    logging.debug(f"Error fetching {symbol} from {name}: {e}")
                    
                    # Update exchange status
                    with app.app_context():
                        db_exchange = Exchange.query.filter_by(name=name).first()
                        if db_exchange:
                            db_exchange.status = 'error'
                            db_exchange.last_check = datetime.utcnow()
        
        with app.app_context():
            db.session.commit()
        
        return all_prices
    
    def find_arbitrage_opportunities(self, prices):
        """Find arbitrage opportunities"""
        opportunities = []
        
        for symbol, exchange_prices in prices.items():
            exchanges = list(exchange_prices.keys())
            
            # Compare every pair of exchanges
            for i in range(len(exchanges)):
                for j in range(i + 1, len(exchanges)):
                    ex1, ex2 = exchanges[i], exchanges[j]
                    
                    if ex1 in exchange_prices and ex2 in exchange_prices:
                        p1 = exchange_prices[ex1]
                        p2 = exchange_prices[ex2]
                        
                        # Scenario 1: Buy on ex1, sell on ex2
                        if p1['ask'] and p2['bid']:
                            profit1 = ((p2['bid'] - p1['ask']) / p1['ask']) * 100
                            
                            if profit1 > self.min_profit_threshold:
                                trade_size = min(1000, (p1.get('volume', 0) + p2.get('volume', 0)) * 0.005)
                                potential_profit = trade_size * profit1 / 100
                                
                                opportunities.append({
                                    'symbol': symbol,
                                    'buy_exchange': ex1,
                                    'sell_exchange': ex2,
                                    'buy_price': p1['ask'],
                                    'sell_price': p2['bid'],
                                    'profit_pct': profit1,
                                    'volume': min(p1.get('volume', 0), p2.get('volume', 0)),
                                    'potential_profit': potential_profit
                                })
                        
                        # Scenario 2: Buy on ex2, sell on ex1
                        if p2['ask'] and p1['bid']:
                            profit2 = ((p1['bid'] - p2['ask']) / p2['ask']) * 100
                            
                            if profit2 > self.min_profit_threshold:
                                trade_size = min(1000, (p1.get('volume', 0) + p2.get('volume', 0)) * 0.005)
                                potential_profit = trade_size * profit2 / 100
                                
                                opportunities.append({
                                    'symbol': symbol,
                                    'buy_exchange': ex2,
                                    'sell_exchange': ex1,
                                    'buy_price': p2['ask'],
                                    'sell_price': p1['bid'],
                                    'profit_pct': profit2,
                                    'volume': min(p1.get('volume', 0), p2.get('volume', 0)),
                                    'potential_profit': potential_profit
                                })
        
        return sorted(opportunities, key=lambda x: x['profit_pct'], reverse=True)
    
    def save_opportunities(self, opportunities):
        """Save opportunities to database"""
        if not opportunities:
            return
        
        with app.app_context():
            for opp in opportunities:
                # Get exchange IDs
                buy_exchange = Exchange.query.filter_by(name=opp['buy_exchange']).first()
                sell_exchange = Exchange.query.filter_by(name=opp['sell_exchange']).first()
                
                if buy_exchange and sell_exchange:
                    opportunity = ArbitrageOpportunity(
                        symbol=opp['symbol'],
                        buy_exchange_id=buy_exchange.id,
                        sell_exchange_id=sell_exchange.id,
                        buy_price=opp['buy_price'],
                        sell_price=opp['sell_price'],
                        profit_percentage=opp['profit_pct'],
                        volume=opp['volume'],
                        potential_profit=opp['potential_profit']
                    )
                    db.session.add(opportunity)
            
            # Update stats
            stats = MonitoringStats.query.first()
            if not stats:
                stats = MonitoringStats()
                db.session.add(stats)
            
            stats.total_opportunities += len(opportunities)
            stats.total_profit_found += sum(opp['profit_pct'] for opp in opportunities)
            stats.monitoring_cycles += 1
            stats.last_update = datetime.utcnow()
            
            # Update best opportunity
            best_profit = max(opp['profit_pct'] for opp in opportunities)
            if best_profit > stats.best_opportunity_profit:
                stats.best_opportunity_profit = best_profit
            
            db.session.commit()
            
            logging.info(f"💰 Found {len(opportunities)} opportunities, best: {best_profit:.3f}%")
    
    def cleanup_old_data(self):
        """Clean up old data to prevent database growth"""
        with app.app_context():
            # Keep only last 7 days of price data
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            PriceData.query.filter(PriceData.timestamp < cutoff_date).delete()
            
            # Keep only last 30 days of opportunities
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            ArbitrageOpportunity.query.filter(ArbitrageOpportunity.timestamp < cutoff_date).delete()
            
            db.session.commit()
    
    def run(self):
        """Main monitoring loop"""
        self.running = True
        self.initialize_exchanges()
        
        if not self.exchanges:
            logging.error("No exchanges available. Stopping monitor.")
            return
        
        cycle = 0
        last_cleanup = datetime.utcnow()
        
        logging.info(f"🚀 Monitor started! Checking every {self.check_interval} seconds")
        
        while self.running:
            try:
                cycle += 1
                logging.debug(f"Monitoring cycle #{cycle}")
                
                # Get prices
                prices = self.get_prices()
                
                # Find opportunities
                opportunities = self.find_arbitrage_opportunities(prices)
                
                # Save opportunities
                if opportunities:
                    self.save_opportunities(opportunities)
                
                # Cleanup old data every hour
                if (datetime.utcnow() - last_cleanup).total_seconds() > 3600:
                    self.cleanup_old_data()
                    last_cleanup = datetime.utcnow()
                
                # Wait for next cycle
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logging.info("Monitor stopped by user")
                self.running = False
                break
            except Exception as e:
                logging.error(f"Error in monitoring cycle: {e}")
                time.sleep(30)  # Wait before retrying

# Global monitor instance
monitor = None

def start_monitoring():
    """Start monitoring in a separate thread"""
    global monitor
    
    def monitor_thread():
        global monitor
        monitor = CryptoMonitor()
        monitor.run()
    
    thread = threading.Thread(target=monitor_thread, daemon=True)
    thread.start()
    logging.info("🔭 Monitoring thread started")

def stop_monitoring():
    """Stop monitoring"""
    global monitor
    if monitor:
        monitor.running = False
        logging.info("Monitor stopped")
