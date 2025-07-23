"""
🔍 DIAGNOSTICA OBSERVATORY BOT - Esegui questo per capire il problema
"""

import ccxt
import time
from datetime import datetime

print("🔍 DIAGNOSTICA OBSERVATORY BOT")
print("="*50)

# Test 1: Connessione Exchange
print("\n1️⃣ TEST CONNESSIONI:")
exchanges_ok = {}
for name in ['binance', 'kraken', 'kucoin', 'mexc']:
    try:
        exchange = getattr(ccxt, name)({'enableRateLimit': True})
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ {name}: OK - BTC @ ${ticker['last']:,.2f}")
        exchanges_ok[name] = exchange
    except Exception as e:
        print(f"❌ {name}: ERRORE - {str(e)[:50]}")

# Test 2: Verifica Spread Reali
print("\n2️⃣ TEST SPREAD REALI:")
if len(exchanges_ok) >= 2:
    # Prendi prezzi BTC/USDT
    prices = {}
    for name, ex in exchanges_ok.items():
        try:
            ticker = ex.fetch_ticker('BTC/USDT')
            prices[name] = {
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread': (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100 if ticker['bid'] else 0
            }
            print(f"{name}: Bid=${ticker['bid']:,.2f} Ask=${ticker['ask']:,.2f} Spread={prices[name]['spread']:.3f}%")
        except:
            pass
    
    # Test 3: Calcola Arbitraggi
    print("\n3️⃣ OPPORTUNITÀ CROSS-EXCHANGE:")
    opps_found = 0
    exchanges = list(prices.keys())
    
    for i in range(len(exchanges)):
        for j in range(i+1, len(exchanges)):
            ex1, ex2 = exchanges[i], exchanges[j]
            
            # Compra su ex1, vendi su ex2
            if prices[ex1]['ask'] and prices[ex2]['bid']:
                profit = ((prices[ex2]['bid'] - prices[ex1]['ask']) / prices[ex1]['ask']) * 100
                print(f"\nCompra {ex1} @ ${prices[ex1]['ask']:,.2f}, Vendi {ex2} @ ${prices[ex2]['bid']:,.2f}")
                print(f"Profitto LORDO: {profit:.4f}%")
                
                # Considera fee (0.1% per exchange = 0.2% totale)
                net_profit = profit - 0.2
                print(f"Profitto NETTO (dopo fee 0.2%): {net_profit:.4f}%")
                
                if net_profit > 0:
                    print(f"🎯 OPPORTUNITÀ REALE!")
                    opps_found += 1
            
            # Compra su ex2, vendi su ex1
            if prices[ex2]['ask'] and prices[ex1]['bid']:
                profit = ((prices[ex1]['bid'] - prices[ex2]['ask']) / prices[ex2]['ask']) * 100
                print(f"\nCompra {ex2} @ ${prices[ex2]['ask']:,.2f}, Vendi {ex1} @ ${prices[ex1]['bid']:,.2f}")
                print(f"Profitto LORDO: {profit:.4f}%")
                net_profit = profit - 0.2
                print(f"Profitto NETTO: {net_profit:.4f}%")
                
                if net_profit > 0:
                    print(f"🎯 OPPORTUNITÀ REALE!")
                    opps_found += 1

# Test 4: Check Database
print("\n4️⃣ TEST DATABASE:")
try:
    import sqlite3
    conn = sqlite3.connect('arbitrage.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"✅ Database esiste. Tabelle: {[t[0] for t in tables]}")
    
    # Check opportunities
    try:
        cursor.execute("SELECT COUNT(*) FROM arbitrage_opportunity")
        count = cursor.fetchone()[0]
        print(f"📊 Opportunità salvate: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM arbitrage_opportunity ORDER BY timestamp DESC LIMIT 3")
            recent = cursor.fetchall()
            print("Ultime 3 opportunità:")
            for opp in recent:
                print(f"  {opp}")
    except Exception as e:
        print(f"⚠️ Errore nel leggere opportunità: {e}")
    
    conn.close()
except Exception as e:
    print(f"❌ Errore database: {e}")

# DIAGNOSI FINALE
print("\n" + "="*50)
print("🏁 DIAGNOSI COMPLETA:")
print("="*50)

if len(exchanges_ok) < 2:
    print("❌ PROBLEMA: Meno di 2 exchange connessi!")
    print("   SOLUZIONE: Verifica connessione internet")
elif opps_found == 0:
    print("⚠️  PROBLEMA: Exchange connessi ma nessuna opportunità")
    print("   POSSIBILI CAUSE:")
    print("   1. Soglia troppo alta (prova 0.05% invece di 0.1%)")
    print("   2. Il bot non salva correttamente")
    print("   3. Periodo di bassa volatilità")
else:
    print("✅ Tutto funziona! Trovate opportunità!")

print("\n💡 PROSSIMO STEP: Ottimizzazione in corso...")