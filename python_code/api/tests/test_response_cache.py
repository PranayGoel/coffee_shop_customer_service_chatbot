import unittest

from response_cache import cache_by_last_message


class FakeAgent:
    def __init__(self):
        self.call_count = 0

    @cache_by_last_message
    def get_response(self, messages):
        self.call_count += 1
        return {"content": f"response #{self.call_count}"}


class TestCacheByLastMessage(unittest.TestCase):
    def setUp(self):
        # The decorator's cache is a closure created once at class-definition time
        # (shared across every FakeAgent instance and every test in this run) --
        # clear it before each test so tests don't see each other's cached keys.
        FakeAgent.get_response.cache_clear()

    def test_repeat_identical_message_hits_cache(self):
        agent = FakeAgent()
        r1 = agent.get_response([{"content": "what are your hours"}])
        r2 = agent.get_response([{"content": "what are your hours"}])
        self.assertEqual(r1, r2)
        self.assertEqual(agent.call_count, 1)

    def test_different_message_is_not_cached(self):
        agent = FakeAgent()
        agent.get_response([{"content": "what are your hours"}])
        agent.get_response([{"content": "what's on the menu"}])
        self.assertEqual(agent.call_count, 2)

    def test_case_and_whitespace_insensitive_key(self):
        agent = FakeAgent()
        agent.get_response([{"content": "  What Are Your Hours  "}])
        agent.get_response([{"content": "what are your hours"}])
        self.assertEqual(agent.call_count, 1)

    def test_cache_is_per_decorated_function_not_shared_across_instances_incorrectly(self):
        # NOTE: this decorator's cache is function-level (module-level closure), so
        # two different agent instances of the SAME class share a cache. That's
        # intentional for DetailsAgent (a stateless singleton per process) -- this
        # test documents that behavior rather than silently relying on it.
        agent_a = FakeAgent()
        agent_b = FakeAgent()
        agent_a.get_response([{"content": "shared question"}])
        agent_b.get_response([{"content": "shared question"}])
        self.assertEqual(agent_a.call_count, 1)
        self.assertEqual(agent_b.call_count, 0)


if __name__ == "__main__":
    unittest.main()
