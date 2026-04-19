"""
Tests for Commission Engine.
Verifies accurate calculation of platform fees and commissions.
"""
import pytest
from decimal import Decimal
from app.core.commission_engine import calculate_commission


def test_commission_calculation_standard():
    """Test standard commission calculation with 2% seller commission."""
    base_amount = Decimal("1000.00")
    seller_commission_rate = Decimal("0.02")  # 2%
    
    result = calculate_commission(base_amount, seller_commission_rate)
    
    # Buyer pays: Base * (1 + Seller_Commission + 0.0075)
    # 1000 * (1 + 0.02 + 0.0075) = 1000 * 1.0275 = 1027.50
    expected_buyer_pays = Decimal("1027.50")
    
    # Seller receives: Base * (1 + Seller_Commission - 0.0075)
    # 1000 * (1 + 0.02 - 0.0075) = 1000 * 1.0125 = 1012.50
    expected_seller_receives = Decimal("1012.50")
    
    # Platform fee: 0.75% from each side = 1.5% total
    # 1000 * 0.0075 * 2 = 15.00
    expected_platform_fee = Decimal("15.00")
    
    assert result["buyer_pays"] == expected_buyer_pays
    assert result["seller_receives"] == expected_seller_receives
    assert result["platform_fee_total"] == expected_platform_fee


def test_commission_zero_seller_commission():
    """Test calculation with 0% seller commission."""
    base_amount = Decimal("1000.00")
    seller_commission_rate = Decimal("0")
    
    result = calculate_commission(base_amount, seller_commission_rate)
    
    # Buyer pays: 1000 * (1 + 0 + 0.0075) = 1007.50
    expected_buyer_pays = Decimal("1007.50")
    
    # Seller receives: 1000 * (1 + 0 - 0.0075) = 992.50
    expected_seller_receives = Decimal("992.50")
    
    # Platform fee: 15.00 (still 1.5% total)
    expected_platform_fee = Decimal("15.00")
    
    assert result["buyer_pays"] == expected_buyer_pays
    assert result["seller_receives"] == expected_seller_receives
    assert result["platform_fee_total"] == expected_platform_fee


def test_commission_max_seller_commission():
    """Test calculation with maximum 3.5% seller commission."""
    base_amount = Decimal("1000.00")
    seller_commission_rate = Decimal("0.035")  # 3.5%
    
    result = calculate_commission(base_amount, seller_commission_rate)
    
    # Buyer pays: 1000 * (1 + 0.035 + 0.0075) = 1042.50
    expected_buyer_pays = Decimal("1042.50")
    
    # Seller receives: 1000 * (1 + 0.035 - 0.0075) = 1027.50
    expected_seller_receives = Decimal("1027.50")
    
    # Platform fee: 15.00
    expected_platform_fee = Decimal("15.00")
    
    assert result["buyer_pays"] == expected_buyer_pays
    assert result["seller_receives"] == expected_seller_receives
    assert result["platform_fee_total"] == expected_platform_fee


def test_commission_small_amount():
    """Test calculation with small amount."""
    base_amount = Decimal("10.00")
    seller_commission_rate = Decimal("0.01")  # 1%
    
    result = calculate_commission(base_amount, seller_commission_rate)
    
    # Buyer pays: 10 * (1 + 0.01 + 0.0075) = 10.175
    expected_buyer_pays = Decimal("10.175")
    
    # Seller receives: 10 * (1 + 0.01 - 0.0075) = 10.025
    expected_seller_receives = Decimal("10.025")
    
    # Platform fee: 10 * 0.0075 * 2 = 0.15
    expected_platform_fee = Decimal("0.15")
    
    assert result["buyer_pays"] == expected_buyer_pays
    assert result["seller_receives"] == expected_seller_receives
    assert result["platform_fee_total"] == expected_platform_fee


def test_commission_large_amount():
    """Test calculation with large amount."""
    base_amount = Decimal("100000.00")
    seller_commission_rate = Decimal("0.02")  # 2%
    
    result = calculate_commission(base_amount, seller_commission_rate)
    
    # Buyer pays: 100000 * 1.0275 = 102750.00
    expected_buyer_pays = Decimal("102750.00")
    
    # Seller receives: 100000 * 1.0125 = 101250.00
    expected_seller_receives = Decimal("101250.00")
    
    # Platform fee: 100000 * 0.015 = 1500.00
    expected_platform_fee = Decimal("1500.00")
    
    assert result["buyer_pays"] == expected_buyer_pays
    assert result["seller_receives"] == expected_seller_receives
    assert result["platform_fee_total"] == expected_platform_fee
