const request = require('supertest');
const express = require('express');
const router = require('../routes/sms_send');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Sms Send', () => {
  test('POST /notifications/sms-send returns success', async () => {
    const res = await request(app)
      .post('/notifications/sms-send')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
