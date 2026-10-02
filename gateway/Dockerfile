# gateway/Dockerfile
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/index.js ./
COPY --from=builder /app/package.json ./

EXPOSE 4000
CMD ["node", "index.js"]