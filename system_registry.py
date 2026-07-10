class SystemRegistry:

    def __init__(self):

        self._services = {}

    # --------------------------------------------------

    def register(
        self,
        service,
        instance
    ):

        if service in self._services:

            raise ValueError(
                f"'{service}' is already registered."
            )

        self._services[service] = instance

    # --------------------------------------------------

    def get(
        self,
        service
    ):

        return self._services.get(service)

    # --------------------------------------------------

    def get_all(self):

        return self._services.values()

    # --------------------------------------------------

    def audit(self):

        return {

            service: instance.__class__.__name__

            for service, instance in self._services.items()

        }