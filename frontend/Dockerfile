FROM node:20-alpine

WORKDIR /app

# Install dependencies (caching)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY . .

# Expose Next.js port
EXPOSE 3000

# Start dev server
CMD ["npm", "run", "dev"]
