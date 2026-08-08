const request = require('supertest');
const express = require('express');
const router = require('../routes/webhook_fire');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Webhook Fire', () => {
  test('POST /notifications/webhook-fire returns success', async () => {
    const res = await request(app)
      .post('/notifications/webhook-fire')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
