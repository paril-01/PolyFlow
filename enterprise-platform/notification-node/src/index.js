const express = require('express');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const app = express();
const PORT = process.env.PORT || 8087;

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()],
});

app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ service: 'notification-node', status: 'healthy', version: '1.6.3' });
});

app.listen(PORT, () => {
  logger.info(`notification-node listening on port ${PORT}`);
});
