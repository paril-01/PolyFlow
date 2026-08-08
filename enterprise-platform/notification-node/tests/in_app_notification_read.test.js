const request = require('supertest');
const express = require('express');
const router = require('../routes/in_app_notification_read');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('In App Notification Read', () => {
  test('POST /notifications/in-app-notification-read returns success', async () => {
    const res = await request(app)
      .post('/notifications/in-app-notification-read')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
