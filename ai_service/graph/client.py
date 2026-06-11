"""
Singleton Neo4j driver — call get_driver() anywhere in the project.
"""
from neo4j import GraphDatabase

_driver = None


def get_driver(uri: str = '', user: str = '', password: str = ''):
    global _driver
    if _driver is None:
        from django.conf import settings
        _driver = GraphDatabase.driver(
            uri      or settings.NEO4J_URI,
            auth=(user or settings.NEO4J_USER,
                  password or settings.NEO4J_PASSWORD),
        )
    return _driver


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
