FROM node:22-slim

WORKDIR /app

# Install required dependencies for Next.js SWC
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade npm to fix bundled dependency vulnerabilities
# (cross-spawn, glob, minimatch, tar)
RUN npm install -g npm@latest

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

# Remove stale build artifacts
RUN rm -rf .next

COPY . .

# Remove any stale .next that came from copy
RUN rm -rf .next

EXPOSE 3000

ENV HOSTNAME=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Run Next.js dev server with exec form for proper signal handling
CMD ["node", "node_modules/next/dist/bin/next", "dev", "-H", "0.0.0.0", "-p", "3000"]
