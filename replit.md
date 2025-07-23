# Crypto Arbitrage Observatory

## Overview

This is a Flask-based cryptocurrency arbitrage monitoring system that automatically tracks price differences across multiple exchanges to identify profit opportunities. The application continuously monitors crypto prices using the CCXT library and provides a real-time dashboard for viewing arbitrage opportunities.

## System Architecture

The application follows a monolithic Flask architecture with the following key components:

- **Web Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (configurable to PostgreSQL via environment variables)
- **Real-time Monitoring**: Background threading for continuous price monitoring
- **Frontend**: Bootstrap-based responsive dashboard with Chart.js visualizations
- **Exchange Integration**: CCXT library for connecting to multiple cryptocurrency exchanges

## Key Components

### Backend Components

1. **Flask Application (`app.py`)**
   - Main application factory with database initialization
   - Proxy fix middleware for deployment compatibility
   - Session management with configurable secret key

2. **Database Models (`models.py`)**
   - `Exchange`: Stores exchange information and status
   - `PriceData`: Real-time price data from exchanges
   - `ArbitrageOpportunity`: Identified profit opportunities
   - `MonitoringStats`: System statistics and performance metrics

3. **Monitoring Engine (`monitor.py`)**
   - Background thread for continuous price monitoring
   - Auto-installation of dependencies (ccxt, pandas)
   - Exchange initialization and health checking
   - Arbitrage opportunity detection logic

4. **API Routes (`routes.py`)**
   - `/api/opportunities`: Returns recent arbitrage opportunities
   - `/api/stats`: System monitoring statistics
   - Dashboard endpoint for main interface

### Frontend Components

1. **Dashboard Interface (`templates/dashboard.html`)**
   - Real-time statistics display
   - Arbitrage opportunities table
   - System status indicators
   - Responsive design with Bootstrap 5

2. **Styling (`static/css/style.css`)**
   - Dark theme optimized for trading platforms
   - Custom CSS variables for consistent theming
   - Responsive design principles

3. **JavaScript (`static/js/dashboard.js`)**
   - Real-time data updates via AJAX
   - Chart.js integration for visualizations
   - Periodic refresh mechanisms

## Data Flow

1. **Price Collection**: Monitor service continuously fetches prices from exchanges (Binance, KuCoin, Kraken, MEXC)
2. **Opportunity Detection**: System compares prices across exchanges to identify arbitrage opportunities
3. **Data Storage**: Opportunities and price data are stored in SQLite database
4. **API Serving**: Flask routes serve data to frontend via JSON APIs
5. **Real-time Updates**: Frontend polls APIs every 30-60 seconds for fresh data

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **CCXT**: Cryptocurrency exchange connectivity
- **Pandas**: Data analysis and manipulation

### Frontend Dependencies (CDN)
- **Bootstrap 5**: UI framework and responsive design
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization and charting

### Monitored Exchanges
- Binance
- KuCoin  
- Kraken
- MEXC

### Tracked Trading Pairs
- BTC/USDT
- ETH/USDT
- BNB/USDT
- SOL/USDT
- MATIC/USDT

## Deployment Strategy

The application is designed for easy deployment on Replit and similar platforms:

1. **Auto-dependency Installation**: Monitor service automatically installs required packages
2. **Environment Configuration**: Database URL and session secrets via environment variables
3. **Proxy Compatibility**: ProxyFix middleware for reverse proxy deployments
4. **Zero Configuration**: Works out-of-the-box with SQLite, upgradeable to PostgreSQL

### Configuration Options
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `SESSION_SECRET`: Flask session encryption key
- Monitoring parameters: Check intervals, profit thresholds, exchange selection

## Changelog
- July 17, 2025: Fixed critical issues and optimized arbitrage detection
  - Resolved database table creation problem
  - Lowered profit threshold from 0.1% to 0.05% for more sensitive detection
  - Fixed JavaScript console errors with proper data handling
  - Improved UI feedback with "Raccolta dati in corso..." messages
  - System now actively detecting and storing arbitrage opportunities
- July 04, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.