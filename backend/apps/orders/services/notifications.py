"""Notification hooks. Log-only for now; plug WhatsApp / push in here later."""

import logging

logger = logging.getLogger(__name__)


def notify_new_order(order) -> None:
    logger.info("New order #%s total=%s customer=%s", order.number, order.total, order.customer_id)
