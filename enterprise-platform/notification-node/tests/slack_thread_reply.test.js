const request = require('supertest');
const express = require('express');
const router = require('../routes/slack_thread_reply');

const app = express();
app.use(express.json());
app.use('/notifications', router);

describe('Slack Thread Reply', () => {
  test('POST /notifications/slack-thread-reply returns success', async () => {
    const res = await request(app)
      .post('/notifications/slack-thread-reply')
      .send({ test: true });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  });
});
