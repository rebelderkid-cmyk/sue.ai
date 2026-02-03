# Stage 1: Builder
# Use official Golang image to compile the binary
FROM golang:alpine AS builder

# Set working directory
WORKDIR /app

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the source code
COPY . .

# Build the Go app
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server ./cmd/server

# Stage 2: Runner
# Use a minimal "distroless" image for security and size (contains only root certs & timezone)
FROM gcr.io/distroless/static-debian12

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/server .
# Copy the service account key
COPY --from=builder /app/service-account.json .

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# Run the binary
CMD ["./server"]
