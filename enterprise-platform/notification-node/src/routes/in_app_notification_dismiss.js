const express = require('express');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * POST /notifications/in-app-notification-dismiss
 * In App Notification Dismiss
 */
router.post('/in-app-notification-dismiss', async (req, res) => {
  const start = Date.now();
  const traceId = uuidv4().slice(0, 8);
  logger.info(`[${traceId}] Processing in_app_notification_dismiss`);

  try {
    const result = await processInAppNotificationDismiss(req.body);
    const elapsed = Date.now() - start;
    res.json({
      status: 'success',
      trace_id: traceId,
      result,
      processing_time_ms: elapsed,
    });
  } catch (err) {
    logger.error(`[${traceId}] in_app_notification_dismiss failed: ${err.message}`);
    res.status(500).json({ status: 'error', error: err.message });
  }
});

async function processInAppNotificationDismiss(payload) {
  return {
    feature: 'in_app_notification_dismiss',
    domain: 'notifications',
    processed: true,
    input_keys: Object.keys(payload || {}),
  };
}

module.exports = router;
