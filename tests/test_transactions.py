import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# استيراد النماذج من الملف الرئيسي
from app.models import User, Order, Transaction, ExchangeRate, AuditLog
from app.models import UserRole, OrderStatus, OrderType, TransactionStatus

pytestmark = pytest.mark.asyncio

class TestTransactionEscrowFlow:
    """اختبارات سيناريو الـ Escrow الكامل (Match -> Lock -> Release)."""

    async def test_full_escrow_flow(self, db_session: AsyncSession):
        """اختبار التدفق الكامل للمعاملة من المطابقة حتى الإتمام."""

        # 1. إنشاء مستخدمين (Buyer و Seller)
        buyer = User(
            username="buyer_test",
            email="buyer@test.com",
            password_hash="hashed_pw",
            role=UserRole.USER,
            public_display_name="Buyer_01"
        )
        seller = User(
            username="seller_test",
            email="seller@test.com",
            password_hash="hashed_pw",
            role=UserRole.USER,
            public_display_name="Seller_01"
        )
        db_session.add(buyer)
        db_session.add(seller)
        await db_session.commit()
        await db_session.refresh(buyer)
        await db_session.refresh(seller)

        # 2. إنشاء سعر صرف
        exchange_rate = ExchangeRate(
            base_currency="USD",
            target_currency="ILS",
            rate=Decimal("3.65"),
            updated_by=admin_user.id if (admin_user := await db_session.execute(
                db_session.query(User).filter(User.role == UserRole.ADMIN)
            ).first()) else 1
        )
        # ملاحظة: في اختبار حقيقي، ننشئ Admin أولاً
        db_session.add(exchange_rate)
        await db_session.commit()

        # 3. إنشاء طلب بيع
        order = Order(
            user_id=seller.id,
            order_type=OrderType.SELL,
            amount_min=Decimal("100.00"),
            amount_max=Decimal("1000.00"),
            commission_rate=Decimal("0.02"),  # 2%
            currency="USD",
            blockchain_network="TRX",
            status=OrderStatus.ACTIVE,
            proof_of_funds_url="https://cloudinary.com/proof.jpg"
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # 4. مطابقة الطلب (Match) - يقوم به Buyer
        transaction = Transaction(
            order_id=order.id,
            buyer_id=buyer.id,
            seller_id=seller.id,
            amount=Decimal("500.00"),
            exchange_rate=Decimal("3.65"),
            status=TransactionStatus.MATCHED,
            buyer_pays=Decimal("513.75"),  # 500 * 1.0275
            seller_receives=Decimal("506.25"),  # 500 * 1.0125
            platform_fee=Decimal("7.50")
        )
        db_session.add(transaction)

        # تحديث حالة الطلب إلى LOCKED
        order.status = OrderStatus.LOCKED
        await db_session.commit()
        await db_session.refresh(transaction)

        assert transaction.status == TransactionStatus.MATCHED
        assert order.status == OrderStatus.LOCKED

        # 5. قفل الضمان (Escrow Lock) - يقوم به Admin
        transaction.status = TransactionStatus.ESCROW_LOCKED
        audit_log = AuditLog(
            user_id=1,  # Admin ID
            action="ESCROW_LOCKED",
            details=f"Transaction {transaction.id} locked by admin",
            ip_address="127.0.0.1"
        )
        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(transaction)

        assert transaction.status == TransactionStatus.ESCROW_LOCKED

        # 6. إطلاق الأموال (Release) - يقوم به Admin
        transaction.status = TransactionStatus.COMPLETED
        audit_log_release = AuditLog(
            user_id=1,
            action="FUNDS_RELEASED",
            details=f"Funds released for transaction {transaction.id}",
            ip_address="127.0.0.1"
        )
        db_session.add(audit_log_release)
        await db_session.commit()
        await db_session.refresh(transaction)

        assert transaction.status == TransactionStatus.COMPLETED

        # 7. التحقق من سجلات التدقيق
        audit_logs = await db_session.execute(
            db_session.query(AuditLog).filter(
                AuditLog.details.contains(str(transaction.id))
            )
        )
        logs = audit_logs.all()
        assert len(logs) >= 2  # على الأقل سجلين: lock و release

    async def test_dispute_flow(self, db_session: AsyncSession):
        """اختبار سيناريو النزاع (Dispute)."""

        # إنشاء مستخدمين ومعاملة (مختصرة)
        buyer = User(username="buyer_d", email="bd@test.com", password_hash="pw", role=UserRole.USER)
        seller = User(username="seller_d", email="sd@test.com", password_hash="pw", role=UserRole.USER)
        db_session.add(buyer)
        db_session.add(seller)
        await db_session.commit()

        transaction = Transaction(
            order_id=1,
            buyer_id=buyer.id,
            seller_id=seller.id,
            amount=Decimal("200.00"),
            status=TransactionStatus.ESCROW_LOCKED
        )
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        # فتح نزاع
        transaction.status = TransactionStatus.DISPUTED
        audit_log = AuditLog(
            user_id=1,
            action="DISPUTE_OPENED",
            details=f"Dispute opened for transaction {transaction.id}",
            ip_address="127.0.0.1"
        )
        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(transaction)

        assert transaction.status == TransactionStatus.DISPUTED

        # حل النزاع لصالح البائع (مثلاً)
        transaction.status = TransactionStatus.COMPLETED
        audit_log_resolve = AuditLog(
            user_id=1,
            action="DISPUTE_RESOLVED",
            details=f"Dispute resolved in favor of seller for transaction {transaction.id}",
            ip_address="127.0.0.1"
        )
        db_session.add(audit_log_resolve)
        await db_session.commit()

        assert transaction.status == TransactionStatus.COMPLETED

    async def test_transaction_amount_calculations(self, db_session: AsyncSession):
        """التحقق من صحة حسابات المبالغ في المعاملة."""

        base_amount = Decimal("1000.00")
        commission_rate = Decimal("0.02")  # 2%
        platform_fee_rate = Decimal("0.0075")  # 0.75%

        buyer_pays = base_amount * (1 + commission_rate + platform_fee_rate)
        seller_receives = base_amount * (1 + commission_rate - platform_fee_rate)
        platform_profit = (base_amount * platform_fee_rate) * 2

        assert buyer_pays == Decimal("1027.50")
        assert seller_receives == Decimal("1012.50")
        assert platform_profit == Decimal("15.00")
