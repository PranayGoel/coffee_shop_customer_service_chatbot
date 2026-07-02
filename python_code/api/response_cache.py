"""
A small in-memory response cache for DetailsAgent -- repeated identical questions
("what are your hours", "what's in a latte") skip the embedding call, the Pinecone
query, and the chat completion entirely.

Deliberately simple: process-lifetime, in-memory, no TTL/invalidation. Documented as
a starting point, not a production cache -- the honest scope for this round is
"demonstrably cuts redundant calls for exact-repeat questions", not a full caching
layer with eviction policies.
"""

import functools


def cache_by_last_message(func):
    """
    Decorator for an agent's get_response(self, messages) method: caches on a
    normalized (stripped, lowercased) version of the last message's content.

    Only caches when the result looks safely cacheable, i.e. plain dict responses
    without per-conversation state -- fine for DetailsAgent's stateless Q&A, not
    intended for stateful agents like OrderTakingAgent.
    """
    cache = {}

    @functools.wraps(func)
    def wrapper(self, messages):
        key = messages[-1]["content"].strip().lower()
        if key in cache:
            return cache[key]
        result = func(self, messages)
        cache[key] = result
        return result

    wrapper.cache_clear = cache.clear
    wrapper.cache_info = lambda: {"size": len(cache)}
    return wrapper
