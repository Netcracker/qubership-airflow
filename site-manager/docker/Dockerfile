FROM golang:1.25.7-alpine3.22 as builder

ENV GOSUMDB=off

WORKDIR /workspace

# Copy Go modules manifests
COPY go.mod go.mod
COPY go.sum go.sum

RUN go mod download

# Copy Go source
COPY pkg/ pkg/
COPY main.go main.go

RUN go mod tidy

# Build
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o airflow-site-manager main.go


FROM alpine:3.22.3

ENV USER_UID=1008 \
    USER_NAME=airflow-site-manager

#prepare the user
RUN adduser -S -u ${USER_UID} ${USER_NAME}

RUN mkdir -p /usr/local/bin/site-manager

# install site-manager binary
COPY --from=builder --chown=${USER_UID} /workspace/airflow-site-manager /usr/local/bin/site-manager

RUN chmod g+wx /usr/local/bin/site-manager/airflow-site-manager \
    && chown -hR ${USER_NAME} /usr/local/bin/site-manager/

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/site-manager/airflow-site-manager"]

USER ${USER_UID}