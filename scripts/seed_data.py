"""
Seed Data Script for P2P Palestine
Run this script to populate the database with initial test data.
Usage: python -m scripts.seed_data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.database import get_settings
from app.models import User, Order, Transaction, ExchangeRate, AuditLog, UserRole, OrderStatus, TransactionStatus
from app.core.security import get_password_hash
from datetime import datetime, timedelta

async def seed_data():
    settings = get_settings()
    
    # Ensure we're using asyncpg driver
    db_url = settings.DATABASE_URL
    if not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    # Create engine specifically for seeding (in case main app isn't running)
    engine = create_async_engine(db_url, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🌱 Starting database seeding...")

        # 1. Check if admin already exists
        result = await session.execute(select(User).where(User.role == UserRole.ADMIN))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("👤 Creating Admin User...")
            admin = User(
                username="admin_master",
                email="admin@p2p.palestine",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                public_display_name="Admin_Support",
                is_active=True
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            print(f"✅ Admin created: ID {admin.id}")
        else:
            print(f"ℹ️  Admin already exists: {admin.username}")

        # 2. Create Test Users (Buyer and Seller)
        result = await session.execute(select(User).where(User.username == "test_buyer"))
        buyer = result.scalar_one_or_none()
        
        if not buyer:
            print("👤 Creating Test Buyer...")
            buyer = User(
                username="test_buyer",
                email="buyer@test.com",
                hashed_password=get_password_hash("buyer123"),
                role=UserRole.USER,
                public_display_name="FastTrader_99",
                bank_details={"bank": "Bank of Palestine", "account": "123456789"}, # Encrypted in real app
                crypto_addresses={"TRX": "T9yD14Nj9j7x...", "ETH": "0x71C..."},
                is_active=True
            )
            session.add(buyer)
            
            seller = User(
                username="test_seller",
                email="seller@test.com",
                hashed_password=get_password_hash("seller123"),
                role=UserRole.USER,
                public_display_name="CryptoKing_ILS",
                bank_details={"bank": "Hapoalim", "account": "987654321"},
                crypto_addresses={"TRX": "TKjdnbJx...", "BNB": "bnb1..."},
                is_active=True
            )
            session.add(seller)
            await session.commit()
            await session.refresh(buyer)
            await session.refresh(seller)
            print(f"✅ Users created: Buyer ({buyer.id}), Seller ({seller.id})")
        else:
            print("ℹ️  Test users already exist.")
            # Fetch seller if buyer exists (assuming both exist or neither)
            result = await session.execute(select(User).where(User.username == "test_seller"))
            seller = result.scalar_one_or_none()

        # 3. Seed Exchange Rates
        rates = [
            {"fiat_currency": "ILS", "rate": 3.65}, # 1 USD = 3.65 ILS
            {"fiat_currency": "JOD", "rate": 0.71}, # 1 USD = 0.71 JOD
        ]
        
        for r in rates:
            result = await session.execute(select(ExchangeRate).where(ExchangeRate.fiat_currency == r["fiat_currency"]))
            existing_rate = result.scalar_one_or_none()
            if not existing_rate:
                new_rate = ExchangeRate(
                    fiat_currency=r["fiat_currency"],
                    rate=r["rate"],
                    updated_by=admin.id
                )
                session.add(new_rate)
                print(f"💱 Added Rate: 1 USD = {r['rate']} {r['fiat_currency']}")
        
        await session.commit()

        # 4. Create a Sample Active Order (Seller wants to sell USDT for ILS)
        result = await session.execute(select(Order).where(Order.seller_id == seller.id))
        orders = result.scalars().all()
        
        if not orders:
            print("📝 Creating Sample Sell Order...")
            sample_order = Order(
                seller_id=seller.id,
                order_type="SELL", # Selling USDT
                currency="ILS",
                blockchain_network="TRX",
                min_amount=50.0,
                max_amount=5000.0,
                commission=1.5, # Seller sets 1.5% commission
                price_per_unit=3.68, # Slightly above market rate
                status=OrderStatus.ACTIVE,
                proof_of_funds_url="https://res.cloudinary.com/demo/image/upload/sample_proof.jpg",
                terms="Please transfer within 15 minutes. Available 9 AM - 9 PM."
            )
            session.add(sample_order)
            await session.commit()
            await session.refresh(sample_order)
            print(f"✅ Order Created: ID {sample_order.id}, Type: {sample_order.order_type}, Currency: {sample_order.currency}")
        else:
            print("ℹ️  Orders already exist for this seller.")
            sample_order = orders[0]

        # 5. Simulate a Transaction (Matching)
        result = await session.execute(select(Transaction).where(Transaction.buyer_id == buyer.id))
        transactions = result.scalars().all()
        
        if not transactions:
            print("🔄 Creating Sample Transaction (Matched)...")
            base_amount = 100.0 # 100 USDT
            
            # Calculate amounts manually to verify logic
            # Buyer Pays = Base * (1 + Seller_Comm + Platform_Fee)
            # Seller Comm = 1.5% (0.015), Platform = 0.75% (0.0075)
            buyer_pays_factor = 1 + 0.015 + 0.0075 # 1.0225
            seller_receives_factor = 1 + 0.015 - 0.0075 # 1.0075
            
            buyer_pays_total = base_amount * buyer_pays_factor # 102.25 USDT value in ILS context usually, but here we store USDT amounts or Fiat?
            # In this schema, we store the 'amount' in USDT and calculate Fiat total separately or store both.
            # Let's assume 'amount' is USDT, and we store the calculated Fiat equivalent.
            
            tx = Transaction(
                order_id=sample_order.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount_usdt=base_amount,
                exchange_rate=sample_order.price_per_unit,
                total_fiat_amount=base_amount * sample_order.price_per_unit * buyer_pays_factor, # Total ILS buyer pays
                seller_receives_fiat=base_amount * sample_order.price_per_unit * seller_receives_factor, # Total ILS seller gets
                platform_fee_fiat=(base_amount * sample_order.price_per_unit) * 0.015, # Total platform fee (1.5% of base value)
                status=TransactionStatus.MATCHED,
                escrow_lock_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            session.add(tx)
            
            # Update Order Status? Usually order becomes 'LOCKED' or removed from list. 
            # For simplicity, we leave order active or add a 'locked_amount' field in real prod. 
            # Here we just create the TX.
            
            audit = AuditLog(
                user_id=buyer.id,
                action="TRANSACTION_CREATED",
                details=f"Buyer matched order {sample_order.id} for {base_amount} USDT"
            )
            session.add(audit)
            
            await session.commit()
            print(f"✅ Transaction Created: ID {tx.id}, Status: {tx.status}")
            print(f"   💰 Buyer Pays (Fiat): {tx.total_fiat_amount:.2f} {sample_order.currency}")
            print(f"   💰 Seller Gets (Fiat): {tx.seller_receives_fiat:.2f} {sample_order.currency}")
            print(f"   🏦 Platform Fee: {tx.platform_fee_fiat:.2f} {sample_order.currency}")

        print("\n🎉 Seeding completed successfully!")
        print("-----------------------------------------")
        print("Login Credentials:")
        print(f"Admin: {admin.username} / admin123")
        print(f"Buyer: {buyer.username} / buyer123")
        print(f"Seller: {seller.username} / seller123")
        print("-----------------------------------------")

if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
