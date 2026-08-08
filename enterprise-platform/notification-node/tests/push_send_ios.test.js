const request = require('supertest');
const express = require('express');
const router = require('../routes/push_send_ios');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Push Send Ios', () => {
  test('POST /notifications/push-send-ios returns success', async () => {
    const res = await request(app)
      .post('/notifications/push-send-ios')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
