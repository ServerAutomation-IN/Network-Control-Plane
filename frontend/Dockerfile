FROM node:20-alpine

WORKDIR /app

# Copy dependency manifests
COPY package.json ./
RUN npm install

# Copy application source code
COPY . .

EXPOSE 3000

CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"]
