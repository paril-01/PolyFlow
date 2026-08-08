const request = require('supertest');
const express = require('express');
const router = require('../routes/sms_delivery_status');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Sms Delivery Status', () => {
  test('POST /notifications/sms-delivery-status returns success', async () => {
    const res = await request(app)
      .post('/notifications/sms-delivery-status')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
