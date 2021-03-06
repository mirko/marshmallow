# -*- coding: utf-8 -*-

import pytest

from marshmallow import fields
from marshmallow.marshalling import Marshaller, Unmarshaller
from marshmallow.exceptions import UnmarshallingError

from tests.base import User

class TestMarshaller:

    @pytest.fixture()
    def marshal(self):
        return Marshaller()

    def test_prefix(self):
        u = User("Foo", email="foo@bar.com")
        marshal = Marshaller(prefix='usr_')
        result = marshal(u, {"email": fields.Email(), 'name': fields.String()})
        assert result['usr_name'] == u.name
        assert result['usr_email'] == u.email

    def test_marshalling_generator(self, marshal):
        gen = (u for u in [User("Foo"), User("Bar")])
        res = marshal(gen, {"name": fields.String()}, many=True)
        assert len(res) == 2

    def test_default_to_missing(self, marshal):
        u = User('Foo', email=None)
        res = marshal(u, {'name': fields.String(),
                         'email': fields.Email(default=fields.missing)})
        assert res['name'] == u.name
        assert 'email' not in res

    def test_serialize_fields_with_load_only_param(self, marshal):
        u = User('Foo', email='foo@bar.com')
        fields_dict = {
            'name': fields.String(),
            'email': fields.Email(load_only=True),
        }
        result = marshal(u, fields_dict)
        assert result['name'] == 'Foo'
        assert 'email' not in result

class TestUnMarshaller:

    @pytest.fixture
    def unmarshal(self):
        return Unmarshaller()

    def test_strict_mode_many(self, unmarshal):
        users = [
            {'email': 'foobar'},
            {'email': 'bar@example.com'}
        ]
        with pytest.raises(UnmarshallingError) as excinfo:
            unmarshal(users, {'email': fields.Email()}, strict=True, many=True)
        assert 'foobar' in str(excinfo)

    def test_stores_errors(self, unmarshal):
        data = {'email': 'invalid-email'}
        unmarshal(data, {"email": fields.Email()})
        assert "email" in unmarshal.errors

    def test_deserialize(self, unmarshal):
        user_data = {
            'age': '12'
        }
        result = unmarshal.deserialize(user_data, {'age': fields.Integer()})
        assert result['age'] == 12

    def test_extra_fields(self, unmarshal):
        data = {'name': 'Mick'}
        fields_dict = {'name': fields.String(), 'age': fields.Integer()}
        # data doesn't have to have all the fields in the schema
        result = unmarshal(data, fields_dict)
        assert result['name'] == data['name']
        assert 'age' not in result

    def test_deserialize_many(self, unmarshal):
        users_data = [
            {'name': 'Mick', 'age': '71'},
            {'name': 'Keith', 'age': '70'}
        ]
        fields_dict = {
            'name': fields.String(),
            'age': fields.Integer(),
        }
        result = unmarshal.deserialize(users_data, fields_dict, many=True)
        assert isinstance(result, list)
        user = result[0]
        assert user['age'] == 71

    def test_deserialize_strict_raises_error(self, unmarshal):
        with pytest.raises(UnmarshallingError):
            unmarshal(
                {'email': 'invalid', 'name': 'Mick'},
                {'email': fields.Email(), 'name': fields.String()},
                strict=True
            )

    def test_deserialize_stores_errors(self, unmarshal):
        user_data = {
            'email': 'invalid',
            'age': 'nan',
            'name': 'Valid Name',
        }
        fields_dict = {
            'email': fields.Email(),
            'age': fields.Integer(),
            'name': fields.String(),
        }
        unmarshal(user_data, fields_dict)
        errors = unmarshal.errors
        assert 'email' in errors
        assert 'age' in errors
        assert 'name' not in errors

    def test_deserialize_fields_with_attribute_param(self, unmarshal):
        data = {
            'username': 'mick@stones.com',
            'name': 'Mick'
        }
        fields_dict = {
            'username': fields.Email(attribute='email'),
            'name': fields.String(attribute='firstname'),
        }
        result = unmarshal.deserialize(data, fields_dict)
        assert result['email'] == 'mick@stones.com'
        assert result['firstname'] == 'Mick'

    def test_deserialize_fields_with_load_from_param(self, unmarshal):
        data = {
            'Name': 'Mick',
            'UserName': 'foo@bar.com',
            'years': '42'
        }
        fields_dict = {
            'name': fields.String(load_from='Name'),
            'username': fields.Email(attribute='email', load_from='UserName'),
            'years': fields.Integer(attribute='age', load_from='Years')
        }
        result = unmarshal.deserialize(data, fields_dict)
        assert result['name'] == 'Mick'
        assert result['email'] == 'foo@bar.com'
        assert result['age'] == 42

    def test_deserialize_fields_with_dump_only_param(self, unmarshal):
        data = {
            'name': 'Mick',
            'years': '42',
        }
        fields_dict = {
            'name': fields.String(),
            'years': fields.Integer(dump_only=True),
        }
        result = unmarshal.deserialize(data, fields_dict)
        assert result['name'] == 'Mick'
        assert 'years' not in result

    def test_preprocessing_function(self, unmarshal):
        data = {'a': 10}
        fields_dict = {
            'a': fields.Integer(),
        }

        def preprocessor(in_vals):
            in_vals['a'] += 1
            return in_vals

        result = unmarshal.deserialize(data, fields_dict, preprocess=[preprocessor])
        assert result['a'] == 11

    def test_preprocessing_many(self, unmarshal):
        data = [
            {'a': 12},
            {'a': 34},
        ]
        fields_dict = {
            'a': fields.Integer(),
        }

        def preprocessor(in_vals):
            in_vals['a'] += 1
            return in_vals

        result = unmarshal.deserialize(data,
            fields_dict, preprocess=[preprocessor], many=True)
        assert result[0]['a'] == 13
        assert result[1]['a'] == 35
