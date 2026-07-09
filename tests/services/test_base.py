"""Unit tests for the base ServiceResult pattern."""

import pytest

from services.base import ServiceResult


@pytest.mark.parametrize(
    "success,data,error",
    [
        (True, "payload", None),
        (False, None, "something went wrong"),
    ],
)
def test_service_result_initialization(success, data, error):
    result = ServiceResult(success=success, data=data, error=error)
    assert result.success is success
    assert result.data == data
    assert result.error == error


def test_service_result_ok_factory():
    result = ServiceResult.ok(data="payload")
    assert result.success is True
    assert result.data == "payload"
    assert result.error is None
    assert result


def test_service_result_fail_factory():
    result = ServiceResult.fail("error message")
    assert result.success is False
    assert result.data is None
    assert result.error == "error message"
    assert not result


def test_service_result_boolean_truthiness():
    assert ServiceResult.ok()
    assert not ServiceResult.fail("error")
