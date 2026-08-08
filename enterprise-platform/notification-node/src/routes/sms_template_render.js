const express = require('express');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * POST /notifications/sms-template-render
 * Sms Template Render
 */
router.post('/sms-template-render', async (req, res) => {
  const start = Date.now();
  const traceId = uuidv4().slice(0, 8);
  logger.info(`[${traceId}] Processing sms_template_render`);

  try {
    const result = await processSmsTemplateRender(req.body);
    const elapsed = Date.now() - start;
    res.json({
      status: 'success',
      trace_id: traceId,
      result,
      processing_time_ms: elapsed,
    });
  } catch (err) {
    logger.error(`[${traceId}] sms_template_render failed: ${err.message}`);
    res.status(500).json({ status: 'error', error: err.message });
  }
});

async function processSmsTemplateRender(payload) {
  return {
    feature: 'sms_template_render',
    domain: 'notifications',
    processed: true,
    input_keys: Object.keys(payload || {}),
  };
}

module.exports = router;
