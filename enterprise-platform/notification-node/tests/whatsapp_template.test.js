const request = require('supertest');
const express = require('express');
const router = require('../routes/whatsapp_template');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Whatsapp Template', () => {
  test('POST /notifications/whatsapp-template returns success', async () => {
    const res = await request(app)
      .post('/notifications/whatsapp-template')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
