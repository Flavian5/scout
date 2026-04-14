FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm ci --only=production

# Copy compiled code (or source if using tsx)
COPY dist/ ./dist/

# Create non-root user for security
RUN addgroup -g 1001 -S discordbot && \
    adduser -S discordbot -u 1001
USER discordbot

EXPOSE 3456

CMD ["node", "dist/index.js"]