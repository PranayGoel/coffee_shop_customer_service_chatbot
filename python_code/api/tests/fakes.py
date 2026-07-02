"""
A minimal, stdlib-only fake replicating just the shape of the `openai` SDK client
(`.chat.completions.create(...).choices[0].message.content`) that llm_client.py and
the agents depend on. Exists so tests never need the real `openai` package
installed -- everything under test here talks to `client` via dependency injection.
"""


class FakeMessage:
    def __init__(self, content=None):
        self.content = content


class FakeChoice:
    def __init__(self, message):
        self.message = message


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(FakeMessage(content=content))]


class FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("FakeCompletions ran out of scripted responses")
        return self._responses.pop(0)


class FakeChat:
    def __init__(self, completions):
        self.completions = completions


class FakeClient:
    """Duck-types the one surface these modules actually touch: client.chat.completions.create(...)."""

    def __init__(self, responses):
        self.chat = FakeChat(FakeCompletions(responses))

    @property
    def calls(self):
        return self.chat.completions.calls


def fake_router_response(content):
    """Convenience: a FakeClient scripted to return one raw JSON string for a router call."""
    return FakeClient([FakeResponse(content)])
