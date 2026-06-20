# YT Insights — production container for Cloud Run
FROM node:22-alpine

WORKDIR /app

# Install production deps only (uses package-lock.json)
COPY package*.json ./
RUN npm ci --omit=dev

# App source
COPY server.js ./
COPY data ./data
COPY public ./public

# Cloud Run injects PORT (defaults to 8080); the server reads process.env.PORT
ENV NODE_ENV=production
EXPOSE 8080

CMD ["node", "server.js"]
