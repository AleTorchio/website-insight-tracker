from datetime import datetime
from app import db

class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    last_check = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PriceData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    bid = db.Column(db.Float)
    ask = db.Column(db.Float)
    volume = db.Column(db.Float, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    exchange = db.relationship('Exchange', backref=db.backref('price_data', lazy=True))

class ArbitrageOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    buy_exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    sell_exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    sell_price = db.Column(db.Float, nullable=False)
    profit_percentage = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Float, default=0)
    potential_profit = db.Column(db.Float, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    buy_exchange = db.relationship('Exchange', foreign_keys=[buy_exchange_id], backref='buy_opportunities')
    sell_exchange = db.relationship('Exchange', foreign_keys=[sell_exchange_id], backref='sell_opportunities')

class MonitoringStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_opportunities = db.Column(db.Integer, default=0)
    total_profit_found = db.Column(db.Float, default=0)
    best_opportunity_profit = db.Column(db.Float, default=0)
    monitoring_cycles = db.Column(db.Integer, default=0)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
