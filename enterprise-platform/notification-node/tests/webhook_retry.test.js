const request = require('supertest');
const express = require('express');
const router = require('../routes/webhook_retry');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Webhook Retry', () => {
  test('POST /notifications/webhook-retry returns success', async () => {
    const res = await request(app)
      .post('/notifications/webhook-retry')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
