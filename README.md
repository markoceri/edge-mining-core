# Edge Mining ⚡️🌞

Software to optimize the use of excess energy, especially from renewable sources, through Bitcoin mining. This system automates the turning on and off of ASIC miner devices based on energy availability, solar forecasts, and user-defined policies.

## Architecture

The project uses **Hexagonal Architecture (Ports and Adapters)** to clearly separate the business logic (Domain and Application Layer) from infrastructural dependencies (Database, external APIs, Hardware Control, User Interfaces).

-   **`edge_mining/domain`**: Contains the pure business logic, subdomains and  their models (Entities, Value Objects), domain exceptions, and the interfaces (Ports) that define the contracts with the outside world.
-   **`edge_mining/application`**: Contains the application services that orchestrate the use cases, utilizing the Domain's Ports.
-   **`test`**: Contains application tests.