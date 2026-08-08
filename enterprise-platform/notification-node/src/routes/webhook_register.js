const express = require('express');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * POST /notifications/webhook-register
 * Webhook Register
 */
router.post('/webhook-register', async (req, res) => {
  const start = Date.now();
  const traceId = uuidv4().slice(0, 8);
  logger.info(`[${traceId}] Processing webhook_register`);

  try {
    const result = await processWebhookRegister(req.body);
    const elapsed = Date.now() - start;
    res.json({
      status: 'success',
      trace_id: traceId,
      result,
      processing_time_ms: elapsed,
    });
  } catch (err) {
    logger.error(`[${traceId}] webhook_register failed: ${err.message}`);
    res.status(500).json({ status: 'error', error: err.message });
  }
});

async function processWebhookRegister(payload) {
  return {
    feature: 'webhook_register',
    domain: 'notifications',
    processed: true,
    input_keys: Object.keys(payload || {}),
  };
}

module.exports = router;
