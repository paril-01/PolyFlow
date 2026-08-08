FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production
COPY . .
EXPOSE 8087
CMD ["node", "src/index.js"]
