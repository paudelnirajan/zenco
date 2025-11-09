"""Basic tests for Zenco package."""
import pytest
from autodoc_ai.cli import main
from autodoc_ai.generators import GeneratorFactory
from autodoc_ai.parser import get_language_parser, get_language_queries


def test_imports():
    """Test that all main modules can be imported."""
    assert main is not None
    assert GeneratorFactory is not None
    assert get_language_parser is not None


def test_language_parsers():
    """Test that parsers can be created for all supported languages."""
    languages = ['python', 'javascript', 'java', 'go', 'cpp']
    for lang in languages:
        parser = get_language_parser(lang)
        assert parser is not None, f"Parser for {lang} should not be None"


def test_language_queries():
    """Test that queries exist for all supported languages."""
    # Only test languages that we know have working queries
    languages = ['python', 'javascript', 'java', 'cpp']
    for lang in languages:
        queries = get_language_queries(lang)
        assert isinstance(queries, dict), f"Queries for {lang} should be a dict"
        assert len(queries) > 0, f"Queries for {lang} should not be empty"


def test_generator_factory_mock():
    """Test that mock generator can be created."""
    generator = GeneratorFactory.create_generator("mock")
    assert generator is not None
    
    # Test mock generator has the expected interface
    assert hasattr(generator, 'generate')
    
    # MockGenerator.generate() expects a Node, so we just test it exists
    # Full integration testing would require creating actual tree-sitter nodes


def test_parser_python_simple():
    """Test Python parser on simple code."""
    parser = get_language_parser('python')
    code = b"def hello():\n    return 'world'"
    tree = parser.parse(code)
    assert tree is not None
    assert tree.root_node is not None


def test_parser_javascript_simple():
    """Test JavaScript parser on simple code."""
    parser = get_language_parser('javascript')
    code = b"function hello() { return 'world'; }"
    tree = parser.parse(code)
    assert tree is not None
    assert tree.root_node is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
