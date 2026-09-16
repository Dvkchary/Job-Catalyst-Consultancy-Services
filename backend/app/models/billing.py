import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import String, Boolean, JSON, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin


class SubscriptionPlan(Base, DatabaseModelMixin):
    """
    Holds SaaS plans configurations: Free, Starter, Professional, Premium, Enterprise, and Custom.
    Also details feature limits: AI Credits, Resume Limits, Job Match Limits, Interview Limits, etc.
    """
    __tablename__ = "subscription_plan"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)  # e.g., 'free', 'starter', 'pro'
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_yearly: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    
    # Feature Limit JSON configuration:
    # {
    #   "ai_credits": 1000,
    #   "resume_limits": 5,
    #   "job_match_limits": 20,
    #   "interview_limits": 2,
    #   "storage_bytes": 10485760,  # 10MB
    #   "api_limits_per_min": 10
    # }
    feature_limits: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Subscription(Base, DatabaseModelMixin):
    """
    Tracks user-specific subscription lifecycle states (trialing, active, paused, canceled, expired).
    Includes synchronization references to Stripe/Razorpay/PayPal.
    """
    __tablename__ = "subscription"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscription_plan.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    status: Mapped[str] = mapped_column(String(50), default="active", index=True, nullable=False)  # active, trialing, paused, canceled, expired
    billing_period: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)  # monthly, yearly, custom
    
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Gateway integrations
    payment_provider: Mapped[str] = mapped_column(String(50), default="stripe", nullable=False)  # stripe, razorpay, paypal, custom
    provider_subscription_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    provider_customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")


class UsageMetric(Base, DatabaseModelMixin):
    """
    Aggregates and meters dynamic usage parameters (AI Tokens, Resume Parsing,
    ATS Analysis, Interview Sessions, API calls, and Storage) for a subscription period.
    """
    __tablename__ = "usage_metric"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscription.id", ondelete="CASCADE"),
        nullable=False
    )
    
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Tracked resource totals:
    ai_credits_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resumes_parsed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ats_analyses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interview_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    job_matches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    api_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    subscription: Mapped["Subscription"] = relationship("Subscription")


class Coupon(Base, DatabaseModelMixin):
    """
    Dynamic referral credits, fixed discounts, and promo code triggers.
    """
    __tablename__ = "coupon"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), default="percentage", nullable=False)  # percentage, fixed, credits
    discount_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_redemptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    redemptions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Invoice(Base, DatabaseModelMixin):
    """
    Enterprise ledger logs mapping subscription bills, receipts, taxes, and pricing elements.
    """
    __tablename__ = "invoice"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("subscription.id", ondelete="SET NULL"),
        nullable=True
    )
    
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="paid", index=True, nullable=False)  # paid, unpaid, refunded, open
    
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    tax: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    discount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    
    # Billing addresses and receipt details
    billing_email: Mapped[str] = mapped_column(String(255), nullable=False)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Gateway specific reference fields
    provider_invoice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription")


class PaymentHistory(Base, DatabaseModelMixin):
    """
    Tracks financial transactions, failures, and refunds for historical audits.
    """
    __tablename__ = "payment_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("invoice.id", ondelete="SET NULL"),
        nullable=True
    )
    
    provider: Mapped[str] = mapped_column(String(50), default="stripe", nullable=False)  # stripe, razorpay, paypal, custom
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="succeeded", nullable=False)  # succeeded, failed, refunded, processing
    
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice")
