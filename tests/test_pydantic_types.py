# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

from unittest import TestCase

from pydantic import BaseModel, ValidationError

from os2mo_fastapi_utils.pydantic_types import Domain, Port


class PortModel(BaseModel):
    port: Port


class DomainModel(BaseModel):
    domain: Domain


class TypeTests(TestCase):
    def test_create_port(self):
        port = Port(80)
        self.assertEqual(repr(port), "Port(80)")
        self.assertEqual(str(port), "80")

        other_port = Port(80)
        self.assertEqual(port, other_port)

        yet_another_port = Port(81)
        self.assertNotEqual(yet_another_port, port)
        self.assertNotEqual(yet_another_port, other_port)

    def test_valid_port(self):
        PortModel(port=80)
        PortModel(port=5432)

    def test_invalid_port(self):
        with self.assertRaises(ValidationError):
            PortModel(port=70000)

        with self.assertRaises(ValidationError):
            PortModel(port="80")

    def test_create_domain(self):
        domain = Domain("example.org")
        self.assertEqual(repr(domain), "Domain('example.org')")
        self.assertEqual(str(domain), "example.org")

        other_domain = Domain("example.org")
        self.assertEqual(domain, other_domain)

        yet_another_domain = Domain("example.com")
        self.assertNotEqual(yet_another_domain, domain)
        self.assertNotEqual(yet_another_domain, other_domain)

    def test_valid_domain(self):
        DomainModel(domain="aa")
        DomainModel(domain="æøå.com")

    def test_invalid_domain(self):
        with self.assertRaises(ValidationError):
            DomainModel(domain=".")

        with self.assertRaises(ValidationError):
            DomainModel(domain=42)
