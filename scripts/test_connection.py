#!/usr/bin/env python3
"""
Test script to verify all connections and integrations
"""

import sys
import os
import logging
from datetime import datetime, date

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import supabase_client
from utils.strategy_loader import strategy_loader
from utils.data_manager import data_manager
from config.settings import settings

logger = logging.getLogger(__name__)


def test_supabase_connection():
    """Test Supabase connection and basic operations"""
    print("🔍 Testing Supabase connection...")
    
    try:
        # Test basic connection
        if not supabase_client.test_connection():
            print("❌ Supabase connection failed")
            return False
        
        print("✅ Supabase connection successful")
        
        # Test table access
        try:
            result = supabase_client.client.table('strategies').select('id, name').limit(1).execute()
            print(f"✅ Strategies table accessible ({len(result.data)} records)")
        except Exception as e:
            print(f"❌ Strategies table access failed: {e}")
            return False
        
        try:
            result = supabase_client.client.table('backtests').select('id').limit(1).execute()
            print(f"✅ Backtests table accessible ({len(result.data)} records)")
        except Exception as e:
            print(f"❌ Backtests table access failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False


def test_minio_connection():
    """Test MinIO connection and data access"""
    print("\n🔍 Testing MinIO connection...")
    
    try:
        # Test basic connection
        if not data_manager.test_connection():
            print("❌ MinIO connection failed")
            return False
        
        print("✅ MinIO connection successful")
        
        # Test available symbols
        symbols = data_manager.get_available_symbols()
        if symbols:
            print(f"✅ Found {len(symbols)} symbols: {symbols[:5]}{'...' if len(symbols) > 5 else ''}")
        else:
            print("⚠️  No symbols found in MinIO")
        
        # Test data info for first symbol
        if symbols:
            symbol = symbols[0]
            timeframes = data_manager.get_available_timeframes(symbol)
            if timeframes:
                timeframe = timeframes[0]
                info = data_manager.get_data_info(symbol, timeframe)
                if info:
                    print(f"✅ Data info for {symbol} {timeframe}: {info['total_rows']} rows, {info['earliest_date']} to {info['latest_date']}")
                else:
                    print(f"⚠️  No data info available for {symbol} {timeframe}")
            else:
                print(f"⚠️  No timeframes found for {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ MinIO test failed: {e}")
        return False


def test_strategy_loading():
    """Test strategy loading from Supabase"""
    print("\n🔍 Testing strategy loading...")
    
    try:
        # Get public strategies
        strategies = supabase_client.get_public_strategies()
        
        if not strategies:
            print("⚠️  No public strategies found in database")
            return True
        
        print(f"✅ Found {len(strategies)} public strategies")
        
        # Test loading first strategy
        strategy = strategies[0]
        strategy_id = strategy['id']
        strategy_name = strategy['name']
        
        try:
            strategy_class = strategy_loader.load_strategy(strategy_id)
            print(f"✅ Successfully loaded strategy: {strategy_name} (class: {strategy_class.__name__})")
            
            # Test strategy validation
            required_methods = ['initialize', 'evaluate_entry', 'evaluate_exit', 'generate_signals']
            for method in required_methods:
                if hasattr(strategy_class, method):
                    print(f"✅ Strategy has required method: {method}")
                else:
                    print(f"❌ Strategy missing required method: {method}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load strategy {strategy_name}: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Strategy loading test failed: {e}")
        return False


def test_data_fetching():
    """Test data fetching from MinIO"""
    print("\n🔍 Testing data fetching...")
    
    try:
        # Get available symbols
        symbols = data_manager.get_available_symbols()
        if not symbols:
            print("⚠️  No symbols available for testing")
            return True
        
        symbol = symbols[0]
        timeframes = data_manager.get_available_timeframes(symbol)
        
        if not timeframes:
            print(f"⚠️  No timeframes available for {symbol}")
            return True
        
        timeframe = timeframes[0]
        
        # Test fetching a small amount of data
        end_date = date.today()
        start_date = date(end_date.year, end_date.month, max(1, end_date.day - 7))  # Last 7 days
        
        try:
            data = data_manager.get_ohlcv_data(symbol, timeframe, start_date, end_date)
            
            if len(data) > 0:
                print(f"✅ Successfully fetched {len(data)} rows of {symbol} {timeframe} data")
                print(f"   Date range: {data['timestamp'][0]} to {data['timestamp'][-1]}")
                print(f"   Columns: {list(data.columns)}")
                return True
            else:
                print(f"⚠️  No data returned for {symbol} {timeframe}")
                return True
                
        except Exception as e:
            print(f"❌ Data fetching failed for {symbol} {timeframe}: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Data fetching test failed: {e}")
        return False


def test_configuration():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        # Test required settings
        required_settings = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY',
            'MINIO_ENDPOINT',
            'MINIO_ACCESS_KEY',
            'MINIO_SECRET_KEY',
            'MINIO_BUCKET'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"❌ Missing required settings: {missing_settings}")
            return False
        
        print("✅ All required settings present")
        
        # Print configuration summary (without sensitive data)
        print(f"   Supabase URL: {settings.SUPABASE_URL}")
        print(f"   MinIO Endpoint: {settings.MINIO_ENDPOINT}")
        print(f"   MinIO Bucket: {settings.MINIO_BUCKET}")
        print(f"   MinIO SSL: {settings.MINIO_USE_SSL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 POC-2 Connection Tests")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_supabase_connection,
        test_minio_connection,
        test_strategy_loading,
        test_data_fetching
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! POC-2 is ready to go!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration and connections.")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = main()
    sys.exit(0 if success else 1)