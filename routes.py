from flask import render_template, jsonify, request
from app import app, db
from models import ArbitrageOpportunity, Exchange, PriceData, MonitoringStats
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/opportunities')
def get_opportunities():
    """Get current arbitrage opportunities"""
    try:
        # Get recent opportunities (last 10 minutes)
        recent_time = datetime.utcnow() - timedelta(minutes=10)
        opportunities = ArbitrageOpportunity.query.filter(
            ArbitrageOpportunity.timestamp >= recent_time
        ).order_by(ArbitrageOpportunity.profit_percentage.desc()).limit(20).all()
        
        result = []
        for opp in opportunities:
            # Get exchange names safely
            buy_exchange = Exchange.query.get(opp.buy_exchange_id)
            sell_exchange = Exchange.query.get(opp.sell_exchange_id)
            
            # Calculate time ago
            time_diff = datetime.utcnow() - opp.timestamp
            if time_diff.seconds < 60:
                time_ago = f"{time_diff.seconds}s ago"
            elif time_diff.seconds < 3600:
                time_ago = f"{time_diff.seconds // 60}m ago"
            else:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            
            result.append({
                'id': opp.id,
                'symbol': opp.symbol,
                'buy_exchange': buy_exchange.name.upper() if buy_exchange else 'Unknown',
                'sell_exchange': sell_exchange.name.upper() if sell_exchange else 'Unknown',
                'buy_price': round(opp.buy_price, 4),
                'sell_price': round(opp.sell_price, 4),
                'profit_percentage': round(opp.profit_percentage, 4),
                'volume': round(opp.volume, 0) if opp.volume else 0,
                'potential_profit': round(opp.potential_profit, 4) if opp.potential_profit else 0,
                'timestamp': opp.timestamp.isoformat(),
                'time_ago': time_ago,
                'profit_class': 'success' if opp.profit_percentage > 0.1 else 'warning' if opp.profit_percentage > 0.05 else 'info'
            })
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting opportunities: {e}")
        return jsonify([])

@app.route('/api/stats')
def get_stats():
    """Get monitoring statistics"""
    try:
        stats = MonitoringStats.query.first()
        if not stats:
            stats = MonitoringStats()
            db.session.add(stats)
            db.session.commit()
        
        # Calculate uptime
        uptime = datetime.utcnow() - stats.start_time
        uptime_hours = uptime.total_seconds() / 3600
        
        # Get exchange statuses
        exchanges = Exchange.query.all()
        exchange_statuses = []
        for exchange in exchanges:
            exchange_statuses.append({
                'name': exchange.name,
                'status': exchange.status,
                'last_check': exchange.last_check.isoformat() if exchange.last_check else None
            })
        
        # Calculate opportunities per hour
        opp_per_hour = stats.total_opportunities / max(1, uptime_hours)
        
        # Get average profit
        avg_profit = stats.total_profit_found / max(1, stats.total_opportunities)
        
        return jsonify({
            'total_opportunities': stats.total_opportunities,
            'avg_profit': round(avg_profit, 3),
            'best_opportunity': round(stats.best_opportunity_profit, 3),
            'uptime_hours': round(uptime_hours, 1),
            'uptime_days': uptime.days,
            'opportunities_per_hour': round(opp_per_hour, 1),
            'monitoring_cycles': stats.monitoring_cycles,
            'exchanges': exchange_statuses,
            'last_update': stats.last_update.isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error getting stats: {e}")
        return jsonify({})

@app.route('/api/price-history/<symbol>')
def get_price_history(symbol):
    """Get price history for a specific symbol"""
    try:
        # Get last 2 hours of data (more recent data for new deployments)
        since = datetime.utcnow() - timedelta(hours=2)
        
        price_data = PriceData.query.filter(
            PriceData.symbol == symbol,
            PriceData.timestamp >= since
        ).order_by(PriceData.timestamp.asc()).all()
        
        # Group by exchange
        exchanges = {}
        for data in price_data:
            exchange_name = data.exchange.name
            if exchange_name not in exchanges:
                exchanges[exchange_name] = []
            
            exchanges[exchange_name].append({
                'timestamp': data.timestamp.isoformat(),
                'price': float(data.price),
                'volume': float(data.volume) if data.volume else 0
            })
        
        # If no data, return current prices from exchanges
        if not exchanges:
            current_prices = PriceData.query.filter(
                PriceData.symbol == symbol
            ).order_by(PriceData.timestamp.desc()).limit(4).all()
            
            for data in current_prices:
                exchange_name = data.exchange.name
                if exchange_name not in exchanges:
                    exchanges[exchange_name] = []
                
                exchanges[exchange_name].append({
                    'timestamp': data.timestamp.isoformat(),
                    'price': float(data.price),
                    'volume': float(data.volume) if data.volume else 0
                })
        
        return jsonify(exchanges)
    except Exception as e:
        app.logger.error(f"Error getting price history: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({})

@app.route('/api/export/opportunities')
def export_opportunities():
    """Export opportunities to CSV"""
    try:
        # Get opportunities from last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        opportunities = ArbitrageOpportunity.query.filter(
            ArbitrageOpportunity.timestamp >= since
        ).all()
        
        # Convert to DataFrame
        data = []
        for opp in opportunities:
            data.append({
                'timestamp': opp.timestamp,
                'symbol': opp.symbol,
                'buy_exchange': opp.buy_exchange.name,
                'sell_exchange': opp.sell_exchange.name,
                'buy_price': opp.buy_price,
                'sell_price': opp.sell_price,
                'profit_percentage': opp.profit_percentage,
                'volume': opp.volume,
                'potential_profit': opp.potential_profit
            })
        
        df = pd.DataFrame(data)
        
        # Create CSV string
        output = StringIO()
        df.to_csv(output, index=False)
        csv_content = output.getvalue()
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=arbitrage_opportunities.csv'}
        )
    except Exception as e:
        app.logger.error(f"Error exporting opportunities: {e}")
        return "Error exporting data", 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
