const request = require('supertest');
const express = require('express');
const router = require('../routes/email_send');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Email Send', () => {
  test('POST /notifications/email-send returns success', async () => {
    const res = await request(app)
      .post('/notifications/email-send')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
