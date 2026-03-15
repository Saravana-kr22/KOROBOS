# KOROBOS — Second Brain Operating System
#
# Copyright (c) 2026 Saravana Perumal K
#
# Licensed under the GNU Affero General Public License v3.

FROM node:22-slim

WORKDIR /app

RUN npm install -g npm@latest

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

COPY . .

# Type-check and export Expo web bundle
RUN npx tsc --noEmit
RUN npx expo export --platform web --output-dir dist

EXPOSE 8081

CMD ["npx", "expo", "start", "--web", "--host", "localhost", "--port", "8081"]
