const request = require('supertest');
const express = require('express');
const router = require('../routes/push_send_android');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Push Send Android', () => {
  test('POST /notifications/push-send-android returns success', async () => {
    const res = await request(app)
      .post('/notifications/push-send-android')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
