const express = require('express');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * POST /notifications/whatsapp-template
 * Whatsapp Template
 */
router.post('/whatsapp-template', async (req, res) => {
  const start = Date.now();
  const traceId = uuidv4().slice(0, 8);
  logger.info(`[${traceId}] Processing whatsapp_template`);

  try {
    const result = await processWhatsappTemplate(req.body);
    const elapsed = Date.now() - start;
    res.json({
      status: 'success',
      trace_id: traceId,
      result,
      processing_time_ms: elapsed,
    });
  } catch (err) {
    logger.error(`[${traceId}] whatsapp_template failed: ${err.message}`);
    res.status(500).json({ status: 'error', error: err.message });
  }
});

async function processWhatsappTemplate(payload) {
  return {
    feature: 'whatsapp_template',
    domain: 'notifications',
    processed: true,
    input_keys: Object.keys(payload || {}),
  };
}

module.exports = router;
