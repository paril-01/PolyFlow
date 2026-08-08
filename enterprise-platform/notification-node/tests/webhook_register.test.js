const request = require('supertest');
const express = require('express');
const router = require('../routes/webhook_register');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Webhook Register', () => {
  test('POST /notifications/webhook-register returns success', async () => {
    const res = await request(app)
      .post('/notifications/webhook-register')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
