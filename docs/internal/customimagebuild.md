# Build Process for Image with Customization

This section describes the steps needed to build Airflow image with customizations.

* Use *FROM* directive in dockerfile with the latest image in [https://github.com/Netcracker/qubership-airflow/releases](https://github.com/Netcracker/qubership-airflow/releases).
* Install the custom libraries.

  **Note**: You can specify the necessary environment variables via Helm charts, so it is not necessary to specify them in the dockerfile.

* Copy/build custom DAGs and necessary files for them.