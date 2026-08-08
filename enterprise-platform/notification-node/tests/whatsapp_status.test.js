const request = require('supertest');
const express = require('express');
const router = require('../routes/whatsapp_status');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Whatsapp Status', () => {
  test('POST /notifications/whatsapp-status returns success', async () => {
    const res = await request(app)
      .post('/notifications/whatsapp-status')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
