import pytest
from decimal import Decimal
from app.core.commission_engine import calculate_commission

class TestCommissionEngine:
    """اختبارات دقيقة لمحرك حساب العمولات."""

    def test_standard_commission_calculation(self):
        """اختبار حساب العمولة القياسي (مبلغ 1000 وعمولة بائع 2%)."""
        base_amount = Decimal("1000.00")
        seller_commission_rate = Decimal("0.02")  # 2%

        result = calculate_commission(base_amount, seller_commission_rate)

        # Buyer Pays = 1000 * (1 + 0.02 + 0.0075) = 1027.50
        expected_buyer_pays = Decimal("1027.50")

        # Seller Receives = 1000 * (1 + 0.02 - 0.0075) = 1012.50
        expected_seller_receives = Decimal("1012.50")

        # Platform Fee = 1000 * 0.0075 = 7.50 (من كل طرف)
        expected_platform_fee = Decimal("7.50")

        assert result["buyer_pays"] == expected_buyer_pays
        assert result["seller_receives"] == expected_seller_receives
        assert result["platform_fee_per_side"] == expected_platform_fee
        assert result["total_platform_profit"] == Decimal("15.00")

    def test_zero_seller_commission(self):
        """اختبار عندما تكون عمولة البائع 0%."""
        base_amount = Decimal("500.00")
        seller_commission_rate = Decimal("0")

        result = calculate_commission(base_amount, seller_commission_rate)

        # Buyer Pays = 500 * (1 + 0 + 0.0075) = 503.75
        assert result["buyer_pays"] == Decimal("503.75")
        # Seller Receives = 500 * (1 + 0 - 0.0075) = 496.25
        assert result["seller_receives"] == Decimal("496.25")
        # Platform Profit = 3.75 + 3.75 = 7.50
        assert result["total_platform_profit"] == Decimal("7.50")

    def test_max_seller_commission(self):
        """اختبار الحد الأقصى لعمولة البائع (3.5%)."""
        base_amount = Decimal("100.00")
        seller_commission_rate = Decimal("0.035")  # 3.5%

        result = calculate_commission(base_amount, seller_commission_rate)

        # Buyer Pays = 100 * (1 + 0.035 + 0.0075) = 104.25
        assert result["buyer_pays"] == Decimal("104.25")
        # Seller Receives = 100 * (1 + 0.035 - 0.0075) = 102.75
        assert result["seller_receives"] == Decimal("102.75")

    def test_small_amount_precision(self):
        """اختبار دقة الحساب مع مبالغ صغيرة."""
        base_amount = Decimal("10.00")
        seller_commission_rate = Decimal("0.01")  # 1%

        result = calculate_commission(base_amount, seller_commission_rate)

        # Buyer Pays = 10 * 1.0175 = 10.175 -> rounds to 10.18
        assert result["buyer_pays"] == Decimal("10.18")
        # Seller Receives = 10 * 1.0025 = 10.025 -> rounds to 10.03 (ROUND_HALF_UP)
        assert result["seller_receives"] == Decimal("10.03")

    def test_large_amount_precision(self):
        """اختبار دقة الحساب مع مبالغ كبيرة."""
        base_amount = Decimal("100000.00")
        seller_commission_rate = Decimal("0.025")  # 2.5%

        result = calculate_commission(base_amount, seller_commission_rate)

        # Buyer Pays = 100000 * 1.0325 = 103250.00
        assert result["buyer_pays"] == Decimal("103250.00")
        # Seller Receives = 100000 * 1.0175 = 101750.00
        assert result["seller_receives"] == Decimal("101750.00")
        # Total Platform Profit = 750 + 750 = 1500
        assert result["total_platform_profit"] == Decimal("1500.00")
