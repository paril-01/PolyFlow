const request = require('supertest');
const express = require('express');
const router = require('../routes/in_app_notification_create');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('In App Notification Create', () => {
  test('POST /notifications/in-app-notification-create returns success', async () => {
    const res = await request(app)
      .post('/notifications/in-app-notification-create')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
