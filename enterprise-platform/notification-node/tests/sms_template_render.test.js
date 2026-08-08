const request = require('supertest');
const express = require('express');
const router = require('../routes/sms_template_render');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Sms Template Render', () => {
  test('POST /notifications/sms-template-render returns success', async () => {
    const res = await request(app)
      .post('/notifications/sms-template-render')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
