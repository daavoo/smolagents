# coding=utf-8
# Copyright 2024 HuggingFace Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import List, Optional, Tuple

import pytest

from smolagents._function_type_hints_utils import get_imports, get_json_schema


def fn_google(x: int, y: Optional[Tuple[str, str, float]] = None) -> None:
    """
    Test function.
    Args:
        x: The first input
        y: The second input.
            With multiline description.
    """
    pass


def fn_numpy(x: int, y: Optional[Tuple[str, str, float]] = None) -> None:
    """Test function.

    Parameters
    ----------
    x : int
        The first input
    y
        The second input.
        With multiline description.
    """
    pass


def fn_rest(x: int, y: Optional[Tuple[str, str, float]] = None) -> None:
    """
    Test function.

    :param x: The first input
    :type x: int
    :param y: The second input.
        With multiline description.
    :type y: int
    """
    pass


@pytest.mark.parametrize("fn", [fn_google, fn_numpy, fn_rest])
def test_get_json_schema(fn):
    schema = get_json_schema(fn)
    expected_schema = {
        "name": fn.__name__,
        "description": "Test function.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "The first input"},
                "y": {
                    "type": "array",
                    "description": "The second input. With multiline description.",
                    "nullable": True,
                    "prefixItems": [{"type": "string"}, {"type": "string"}, {"type": "number"}],
                },
            },
            "required": ["x"],
        },
        "return": {"type": "null"},
    }
    assert schema["function"]["parameters"]["properties"]["y"] == expected_schema["parameters"]["properties"]["y"]
    assert schema["function"] == expected_schema


class TestGetCode:
    @pytest.mark.parametrize(
        "code, expected",
        [
            (
                """
        import numpy
        import pandas
        """,
                ["numpy", "pandas"],
            ),
            # From imports
            (
                """
        from torch import nn
        from transformers import AutoModel
        """,
                ["torch", "transformers"],
            ),
            # Mixed case with nested imports
            (
                """
        import numpy as np
        from torch.nn import Linear
        import os.path
        """,
                ["numpy", "torch", "os"],
            ),
            # Try/except block (should be filtered)
            (
                """
        try:
            import torch
        except ImportError:
            pass
        import numpy
        """,
                ["numpy"],
            ),
            # Flash attention block (should be filtered)
            (
                """
        if is_flash_attn_2_available():
            from flash_attn import flash_attn_func
        import transformers
        """,
                ["transformers"],
            ),
            # Relative imports (should be excluded)
            (
                """
        from .utils import helper
        from ..models import transformer
        """,
                [],
            ),
        ],
    )
    def test_get_imports(self, code: str, expected: List[str]):
        assert sorted(get_imports(code)) == sorted(expected)
