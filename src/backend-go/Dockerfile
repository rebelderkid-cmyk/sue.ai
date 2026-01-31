# Stage 1: Builder
# Use official Golang image to compile the binary
FROM golang:1.24-alpine AS builder

# Set working directory
WORKDIR /app

# Copy go mod and sum files
COPY go.mod ./
# COPY go.sum ./ # Uncomment when go.sum exists (after go mod tidy)

# Download dependencies
# RUN go mod download # Uncomment when go.mod is populated

# Copy the source code
COPY . .

# Build the Go app
# -ldflags="-w -s" reduces binary size by stripping debug info
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server ./cmd/server

# Stage 2: Runner
# Use a minimal "distroless" image for security and size (contains only root certs & timezone)
FROM gcr.io/distroless/static-debian12

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/server .

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# Run the binary
CMD ["./server"]
