#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Licensed under the Open Software License ("OSL") v. 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.opensource.org/licenses/osl-3.0.php

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tokenize
from cStringIO import StringIO
import sys
from os.path import dirname, abspath, join
root_path = abspath(join(dirname(__file__), "../../"))
sys.path.insert(0, root_path)

from pynq.expressions import ConstantExpression, BinaryExpression

class ExpressionParser(object):
    def __init__(self):
        self.operators = {
            "+":OperatorAddToken,
            "-":OperatorSubToken,
            "*":OperatorMulToken,
            "/":OperatorDivToken,
            "%":OperatorModToken,
            "**":OperatorPowerToken,
        }
        
    def expression(self, rbp=0):
        global token
        t = token
        token = next()
        left = t.nud()
        while rbp < token.lbp:
            t = token
            token = next()
            left = t.led(left)
        return left

    def parse(self, program):
        global token, next
        next = self.__tokenize(program).next
        token = next()
        return self.expression()

    def __tokenize(self, program):
        for id, value in self.__tokenize_python(program):
            if id == "(literal)":
                yield literal_token(self.expression, value)
            elif id == "(operator)" and self.operators.has_key(value):
                yield self.operators[value](self.expression)
            elif id == "(end)":
                yield end_token(self.expression)
            else:
                raise SyntaxError("unknown operator: %r" % value)

    def __tokenize_python(self, program):
        type_map = {
            tokenize.NUMBER: "(literal)",
            tokenize.STRING: "(literal)",
            tokenize.OP: "(operator)",
            tokenize.NAME: "(name)",
        }
        for t in tokenize.generate_tokens(StringIO(program).next):
            try:
                yield type_map[t[0]], t[1]
            except KeyError:
                if t[0] == tokenize.ENDMARKER:
                    break
                else:
                    raise SyntaxError("Syntax error")
        yield "(end)", "(end)"

class base_token(object):
    def __init__(self, expression):
        self.expression = expression

class literal_token(base_token):
    def __init__(self, expression, value):
        super(literal_token, self).__init__(expression)
        self.value = value
    def nud(self):
        return ConstantExpression(self.value)

class OperatorAddToken(base_token):
    lbp = 110
    def led(self, left):
        return BinaryExpression(BinaryExpression.Add, left, self.expression(self.lbp))

class OperatorSubToken(base_token):
    lbp = 110
    def nud(self):
        return UnaryExpression(UnaryExpression.Negate, self.expression(self.lbp+20))
    def led(self, left):
        return BinaryExpression(BinaryExpression.Subtract, left, self.expression(self.lbp))

class OperatorMulToken(base_token):
    lbp = 120
    def led(self, left):
        return BinaryExpression(BinaryExpression.Multiply, left, self.expression(self.lbp))

class OperatorDivToken(base_token):
    lbp = 120
    def led(self, left):
        return BinaryExpression(BinaryExpression.Divide, left, self.expression(self.lbp))

class OperatorModToken(base_token):
    lbp = 130
    def led(self, left):
        return BinaryExpression(BinaryExpression.Modulo, left, self.expression(self.lbp))

class OperatorPowerToken(base_token):
    lbp = 140
    def led(self, left):
        return BinaryExpression(BinaryExpression.Power, left, self.expression(self.lbp-1))

class end_token(base_token):
    lbp = 0
