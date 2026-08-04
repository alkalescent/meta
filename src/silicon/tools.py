"""Simple greeter module for hello world demonstrations."""


class Greeter:
    """A simple greeter class for hello world demonstrations."""

    def __init__(self, name: str = "World") -> None:
        """Initialize the greeter with a name.

        Args:
            name: The name to greet. Defaults to "World".
        """
        self.name = name

    def greet(self) -> str:
        """Generate a greeting message.

        Returns:
            A greeting string in the format "Hello, {name}!".
        """
        return f"Hello, {self.name}!"

    def farewell(self) -> str:
        """Generate a farewell message.

        Returns:
            A farewell string in the format "Goodbye, {name}!".
        """
        return f"Goodbye, {self.name}!"
