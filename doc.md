## Title & Description
"kafka-notify" - Nuvla notification service. Built on top of Kafka. Send Nuvla custom templated notification messages via Email, Slack, and MQTT. The messages are taken from Kafka topics.
 
## Docker Image Information
- Image name and versioning strategy:
  - `nuvla/kafka-notify:0.9.0`
  - Uses semantic versioning.
 
## Usage
- Basic `docker run` command with required environment variables, ports, and volumes:
  ```sh
  docker run -d --name notify-slack \
    --network backend \
    --env NUVLA_ENDPOINT="${NUVLA_ENDPOINT}" \
    --entrypoint slack \
    --restart unless-stopped \
    nuvla/kafka-notify:0.9.0
  ```
  - Possible values for `entrypoint`: `slack`, `email`, `mqtt`
 
## Configuration
- List of environment variables with descriptions and default values:
  - `NUVLA_ENDPOINT` - Nuvla service public HTTP endpoint. If not provided, defaults to `https://nuvla.io`
 
## Network Configuration
### Exposed Ports
- N/A
 
## Volumes & Persistent Storage
- Required/optional mount points for persistent data:
  - N/A
 
## Dependencies
- Required services:
  - Kafka
 
## Health Checks
- How to check if the service is running & ready:
  - N/A
 
## Security Considerations
- The container runs as:
  - non-root
- Requested elevation:
  - N/A
- Authentication, authorization, and network security notes:
  - N/A
- Is TLS/SSL used for encrypted connections? Where must the certificate be installed?
  - N/A
 
## Logging & Debugging
- Log levels, locations, and debugging options:
  - Logs go to stdout/stderr
 
## Hardware Requirements
- Minimum CPU/RAM requested for the service:
  - 1 vCPU / 500MB RAM
 
## Stateless
- `Yes`
 
## Startup & Dependency Order
- Whether this container requires another service to be up first:
  - Kafka is required, but if not available, the container exits. COE should restart the container.
 
## Scaling & High Availability
- Whether the container can be replicated (multi-instantiated):
  - Supports any number of concurrently run instances.
 
## Affinity with Other Containers
- Whether this service should be scheduled on specific nodes alongside other services:
  - Affinity with other containers is not required.
 
## Example Deployment Configurations
- Sample `docker-compose.yaml` or Kubernetes manifest:
  ```yaml
  notify-slack:
    image: nuvla/kafka-notify:0.9.0
    depends_on:
      - ksqldb-server
    networks:
      - backend
    command:
      - slack
    environment:
      NUVLA_ENDPOINT: "${NUVLA_ENDPOINT}"
  ```
 
## License & Support
- License: Apache 2.0
