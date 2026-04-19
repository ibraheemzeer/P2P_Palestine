"""
Commission engine for P2P Palestine.
Implements the business logic for calculating fees and amounts.

Platform Fee: Fixed at 0.75% per side (Total 1.5% profit)
Math Logic:
    Buyer_Pays = Base_Amount * (1 + Seller_Commission + 0.0075)
    Seller_Receives = Base_Amount * (1 + Seller_Commission - 0.0075)
"""
from decimal import Decimal, ROUND_HALF_UP


# Platform fee constant (0.75% = 0.0075)
PLATFORM_FEE_RATE = Decimal("0.0075")


def calculate_commission(base_amount: float | Decimal, seller_commission: float | Decimal) -> dict:
    """
    Calculate all financial values for a transaction.
    
    Args:
        base_amount: The base USDT amount being traded
        seller_commission: Seller's commission rate (0% - 3.5%, e.g., 0.02 for 2%)
    
    Returns:
        Dictionary with all calculated values
    
    Example:
        If base_amount = 1000 USDT and seller_commission = 0.02 (2%):
        - Buyer_Pays = 1000 * (1 + 0.02 + 0.0075) = 1027.5 USDT
        - Seller_Receives = 1000 * (1 + 0.02 - 0.0075) = 1012.5 USDT
        - Platform_Fee (per side) = 1000 * 0.0075 = 7.5 USDT
        - Total Platform Profit = 15.0 USDT (1.5%)
    """
    # Convert to Decimal for precise calculations
    if not isinstance(base_amount, Decimal):
        base_amount = Decimal(str(base_amount))
    if not isinstance(seller_commission, Decimal):
        seller_commission = Decimal(str(seller_commission))
    
    # Validate inputs
    if base_amount <= 0:
        raise ValueError("Base amount must be positive")
    if seller_commission < 0 or seller_commission > Decimal("0.035"):
        raise ValueError("Seller commission must be between 0% and 3.5%")
    
    # Calculate buyer pays: Base * (1 + Seller_Commission + 0.0075)
    buyer_pays = base_amount * (Decimal("1") + seller_commission + PLATFORM_FEE_RATE)
    
    # Calculate seller receives: Base * (1 + Seller_Commission - 0.0075)
    seller_receives = base_amount * (Decimal("1") + seller_commission - PLATFORM_FEE_RATE)
    
    # Calculate platform fee per side
    platform_fee_per_side = base_amount * PLATFORM_FEE_RATE
    
    # Total platform profit (both sides)
    total_platform_profit = platform_fee_per_side * Decimal("2")
    
    return {
        "base_amount": base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "seller_commission": seller_commission,
        "platform_fee_per_side": platform_fee_per_side.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "buyer_pays": buyer_pays.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "seller_receives": seller_receives.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_platform_profit": total_platform_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }


def validate_order_amount(amount: Decimal, min_amount: Decimal, max_amount: Decimal) -> bool:
    """
    Validate if an amount is within the order's acceptable range.
    
    Args:
        amount: The amount to validate
        min_amount: Minimum acceptable amount
        max_amount: Maximum acceptable amount
    
    Returns:
        True if valid, False otherwise
    """
    return min_amount <= amount <= max_amount


def calculate_seller_commission(order_commission: Decimal, is_buyer_accepting: bool) -> Decimal:
    """
    Determine which commission rate to use based on who is accepting the order.
    
    In our model, the order creator sets their commission rate. This rate applies
    regardless of whether a buyer or seller is accepting the order.
    
    Args:
        order_commission: The commission set by the order creator
        is_buyer_accepting: Whether a buyer is accepting the order
    
    Returns:
        The commission rate to use for calculations
    """
    # The order creator's commission always applies
    return order_commission
