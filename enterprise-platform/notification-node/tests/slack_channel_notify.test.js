const request = require('supertest');
const express = require('express');
const router = require('../routes/slack_channel_notify');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Slack Channel Notify', () => {
  test('POST /notifications/slack-channel-notify returns success', async () => {
    const res = await request(app)
      .post('/notifications/slack-channel-notify')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
