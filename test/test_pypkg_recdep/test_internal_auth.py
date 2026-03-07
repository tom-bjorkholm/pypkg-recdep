#! /usr/local/bin/python3
"""Test authentication classes for internal PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
import pytest
import requests
from pypkg_recdep.internal_server_listing import NoAuth, TokenAuth


def test_noauth_ok1(capsys: pytest.CaptureFixture[str]) -> None:
    """Test NoAuth returns request unchanged."""
    auth = NoAuth()
    req = requests.Request('GET', 'http://example.com/simple').prepare()
    original_headers = deepcopy(req.headers)
    result = auth(req)
    out, err = capsys.readouterr()
    assert result is req
    assert result.headers == original_headers
    assert 'Authorization' not in result.headers
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('url,method',
                         [('http://example.com/simple', 'GET'),
                          ('https://pypi.org/simple', 'POST'),
                          ('http://internal.server/api', 'PUT')])
def test_noauth_ok2(capsys: pytest.CaptureFixture[str], url: str,
                    method: str) -> None:
    """Test NoAuth with different URLs and methods."""
    auth = NoAuth()
    req = requests.Request(method, url).prepare()
    original_headers = deepcopy(req.headers)
    result = auth(req)
    out, err = capsys.readouterr()
    assert result is req
    assert result.headers == original_headers
    assert 'Authorization' not in result.headers
    assert result.method == method
    assert result.url == url
    assert '' == out
    assert '' == err


def test_noauth_with_existing_headers(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test NoAuth preserves existing headers."""
    auth = NoAuth()
    req = requests.Request('GET', 'http://example.com/simple',
                           headers={'User-Agent': 'test-agent',
                                    'Accept': 'application/json'}).prepare()
    original_headers = deepcopy(req.headers)
    result = auth(req)
    out, err = capsys.readouterr()
    assert result is req
    assert result.headers == original_headers
    assert 'User-Agent' in result.headers
    assert result.headers['User-Agent'] == 'test-agent'
    assert 'Accept' in result.headers
    assert result.headers['Accept'] == 'application/json'
    assert 'Authorization' not in result.headers
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('token',
                         ['test_token_123',
                          'abc123def456',
                          'Bearer_token_xyz',
                          'short',
                          'a' * 100])
def test_tokenauth_ok1(capsys: pytest.CaptureFixture[str],
                       token: str) -> None:
    """Test TokenAuth adds authorization header with different tokens."""
    auth = TokenAuth(token=token)
    req = requests.Request('GET', 'http://example.com/simple').prepare()
    result = auth(req)
    out, err = capsys.readouterr()
    assert result is req
    assert 'Authorization' in result.headers
    assert result.headers['Authorization'] == f'Bearer {token}'
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('token,url,method',
                         [('token1', 'http://example.com/simple', 'GET'),
                          ('token2', 'https://pypi.org/simple', 'POST'),
                          ('token3', 'http://internal.server/api', 'PUT'),
                          ('token4', 'https://test.org/packages', 'DELETE')])
def test_tokenauth_ok2(capsys: pytest.CaptureFixture[str], token: str,
                       url: str, method: str) -> None:
    """Test TokenAuth with different tokens, URLs, and methods."""
    auth = TokenAuth(token=token)
    req = requests.Request(method, url).prepare()
    result = auth(req)
    out, err = capsys.readouterr()
    assert result is req
    assert 'Authorization' in result.headers
    assert result.headers['Authorization'] == f'Bearer {token}'
    assert result.method == method
    assert result.url == url
    assert '' == out
    assert '' == err


def test_tokenauth_preserves_headers(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test TokenAuth preserves existing headers."""
    token = 'test_token_preserve'
    auth = TokenAuth(token=token)
    req = requests.Request('GET', 'http://example.com/simple',
                           headers={'User-Agent': 'test-agent',
                                    'Accept': 'application/json',
                                    'Content-Type': 'text/plain'}).prepare()
    result = auth(req)
    out, err = capsys.readouterr()
    assert result is req
    assert 'Authorization' in result.headers
    assert result.headers['Authorization'] == f'Bearer {token}'
    assert 'User-Agent' in result.headers
    assert result.headers['User-Agent'] == 'test-agent'
    assert 'Accept' in result.headers
    assert result.headers['Accept'] == 'application/json'
    assert 'Content-Type' in result.headers
    assert result.headers['Content-Type'] == 'text/plain'
    assert '' == out
    assert '' == err


def test_tokenauth_overwrites_existing_auth(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test TokenAuth overwrites existing Authorization header."""
    token = 'new_token_123'
    auth = TokenAuth(token=token)
    req = requests.Request('GET', 'http://example.com/simple',
                           headers={'Authorization': 'Bearer old_token',
                                    'User-Agent': 'test-agent'}).prepare()
    result = auth(req)
    out, err = capsys.readouterr()
    assert result is req
    assert 'Authorization' in result.headers
    assert result.headers['Authorization'] == f'Bearer {token}'
    assert result.headers['Authorization'] != 'Bearer old_token'
    assert 'User-Agent' in result.headers
    assert result.headers['User-Agent'] == 'test-agent'
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('token',
                         ['token_a', 'token_b', 'token_c'])
def test_tokenauth_multiple_calls(capsys: pytest.CaptureFixture[str],
                                  token: str) -> None:
    """Test TokenAuth can be called multiple times with same instance."""
    auth = TokenAuth(token=token)
    req1 = requests.Request('GET', 'http://example.com/api1').prepare()
    req2 = requests.Request('POST', 'http://example.com/api2').prepare()
    req3 = requests.Request('PUT', 'http://example.com/api3').prepare()
    result1 = auth(req1)
    result2 = auth(req2)
    result3 = auth(req3)
    out, err = capsys.readouterr()
    assert result1 is req1
    assert result1.headers['Authorization'] == f'Bearer {token}'
    assert result1.url == 'http://example.com/api1'
    assert result2 is req2
    assert result2.headers['Authorization'] == f'Bearer {token}'
    assert result2.url == 'http://example.com/api2'
    assert result3 is req3
    assert result3.headers['Authorization'] == f'Bearer {token}'
    assert result3.url == 'http://example.com/api3'
    assert '' == out
    assert '' == err


def test_tokenauth_stores_token(capsys: pytest.CaptureFixture[str]) -> None:
    """Test TokenAuth correctly stores the token."""
    token = 'stored_token_test'
    auth = TokenAuth(token=token)
    out, err = capsys.readouterr()
    assert auth.token == token
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('token1,token2',
                         [('token_x', 'token_y'),
                          ('abc', 'xyz'),
                          ('first', 'second')])
def test_tokenauth_different_instances(capsys: pytest.CaptureFixture[str],
                                       token1: str, token2: str) -> None:
    """Test different TokenAuth instances use their own tokens."""
    auth1 = TokenAuth(token=token1)
    auth2 = TokenAuth(token=token2)
    req1 = requests.Request('GET', 'http://example.com/test1').prepare()
    req2 = requests.Request('GET', 'http://example.com/test2').prepare()
    result1 = auth1(req1)
    result2 = auth2(req2)
    out, err = capsys.readouterr()
    assert result1.headers['Authorization'] == f'Bearer {token1}'
    assert result2.headers['Authorization'] == f'Bearer {token2}'
    assert result1.headers['Authorization'] != result2.headers['Authorization']
    assert '' == out
    assert '' == err
